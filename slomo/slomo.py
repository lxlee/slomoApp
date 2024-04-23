import os
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
from PIL import Image
from .model import UNet, backWarp

def pil_loader(path, cropArea=None, resizeDim=None, frameFlip=0):
    """
    Opens image at `path` using pil and applies data augmentation.

    Parameters
    ----------
        path : string
            path of the image.
        cropArea : tuple, optional
            coordinates for cropping image. Default: None
        resizeDim : tuple, optional
            dimensions for resizing image. Default: None
        frameFlip : int, optional
            Non zero to flip image horizontally. Default: 0

    Returns
    -------
        list
            2D list described above.
    """


    # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
    with open(path, 'rb') as f:
        img = Image.open(f)
        # Resize image if specified.
        resized_img = img.resize(resizeDim, Image.Resampling.LANCZOS) if (resizeDim != None) else img
        # Crop image if crop area specified.
        cropped_img = img.crop(cropArea) if (cropArea != None) else resized_img
        # Flip image horizontally if specified.
        flipped_img = cropped_img.transpose(Image.FLIP_LEFT_RIGHT) if frameFlip else cropped_img
        return flipped_img.convert('RGB')


def load_image(imagePath, transform=None, resizeDim=None):
    image = pil_loader(imagePath, resizeDim=resizeDim)
    # Apply transformation if specified.
    if transform is not None:
        image = transform(image)
    return image.unsqueeze(0)

def get_device_list():
    deviceList = []
    if torch.cuda.is_available():
        for inx in range(torch.cuda.device_count()):
            deviceList.append(f"cuda:{inx}")
    deviceList.append("cpu")
    return deviceList

class Slomo():
    def __init__(self, checkpoint, sf=2, device="cuda:0") -> None:
        self._sf = sf
        if device.startswith("cuda") and not torch.cuda.is_available():
            self._device = torch.device("cpu")
            print(f"Cuda is not available for torch")
        else:
            self._device = torch.device(device)
        
        self._oriDim, self._dim = None, None

        mean = [0.429, 0.431, 0.397]
        std  = [1, 1, 1]
        normalize = transforms.Normalize(mean=mean, std=std)
        
        negmean = [x * -1 for x in mean]
        revNormalize = transforms.Normalize(mean=negmean, std=std)

        # Temporary fix for issue #7 https://github.com/avinashpaliwal/Super-SloMo/issues/7 -
        # - Removed per channel mean subtraction for CPU.
        if (self._device == "cpu"):
            self._transform = transforms.Compose([transforms.ToTensor()])
            self._TP = transforms.Compose([transforms.ToPILImage()])
        else:
            self._transform = transforms.Compose([transforms.ToTensor(), normalize])
            self._TP = transforms.Compose([revNormalize, transforms.ToPILImage()])

        # Initialize model
        self._flowComp = UNet(6, 4)
        self._flowComp.to(device)
        for param in self._flowComp.parameters():
            param.requires_grad = False
        self._ArbTimeFlowIntrp = UNet(20, 5)
        self._ArbTimeFlowIntrp.to(device)
        for param in self._ArbTimeFlowIntrp.parameters():
            param.requires_grad = False

        dict1 = torch.load(checkpoint, map_location=device)
        self._ArbTimeFlowIntrp.load_state_dict(dict1['state_dictAT'])
        self._flowComp.load_state_dict(dict1['state_dictFC'])

    def _checkImg(self, imagePath):
        image = Image.open(imagePath)
        oriDim = image.size
        if self._oriDim != oriDim:
            self._oriDim = oriDim
            self._dim = int(oriDim[0] / 32) * 32, int(oriDim[1] / 32) * 32

            self._flowBackWarp = backWarp(self._dim[0], self._dim[1], self._device)
            self._flowBackWarp = self._flowBackWarp.to(self._device)

    def process(self, firstImage, secondImage, dstDir):
        outputPath = dstDir
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)

        self._checkImg(firstImage)

        # Interpolate frames
        frameCounter = 1
        with torch.no_grad():
            frame0 = load_image(firstImage, self._transform, self._dim)
            frame1 = load_image(secondImage, self._transform, self._dim)

            I0 = frame0.to(self._device)
            I1 = frame1.to(self._device)

            flowOut = self._flowComp(torch.cat((I0, I1), dim=1))
            F_0_1 = flowOut[:,:2,:,:]
            F_1_0 = flowOut[:,2:,:,:]

            # Save reference frames in output folder
            for batchIndex in range(frame0.shape[0]):
                (self._TP(frame0[batchIndex].detach())).resize(self._oriDim, Image.BILINEAR).save(os.path.join(outputPath, str(frameCounter + self._sf * batchIndex) + ".jpg"))
            frameCounter += 1

            # Generate intermediate frames
            for intermediateIndex in range(1, self._sf):
                t = float(intermediateIndex) / self._sf
                temp = -t * (1 - t)
                fCoeff = [temp, t * t, (1 - t) * (1 - t), temp]

                F_t_0 = fCoeff[0] * F_0_1 + fCoeff[1] * F_1_0
                F_t_1 = fCoeff[2] * F_0_1 + fCoeff[3] * F_1_0

                g_I0_F_t_0 = self._flowBackWarp(I0, F_t_0)
                g_I1_F_t_1 = self._flowBackWarp(I1, F_t_1)
                # print(g_I0_F_t_0.shape, g_I1_F_t_1.shape) 
                intrpOut = self._ArbTimeFlowIntrp(torch.cat((I0, I1, F_0_1, F_1_0, F_t_1, F_t_0, g_I1_F_t_1, g_I0_F_t_0), dim=1))
                    
                F_t_0_f = intrpOut[:, :2, :, :] + F_t_0
                F_t_1_f = intrpOut[:, 2:4, :, :] + F_t_1
                V_t_0   = torch.sigmoid(intrpOut[:, 4:5, :, :])
                V_t_1   = 1 - V_t_0
                    
                g_I0_F_t_0_f = self._flowBackWarp(I0, F_t_0_f)
                g_I1_F_t_1_f = self._flowBackWarp(I1, F_t_1_f)
                
                wCoeff = [1 - t, t]

                Ft_p = (wCoeff[0] * V_t_0 * g_I0_F_t_0_f + wCoeff[1] * V_t_1 * g_I1_F_t_1_f) / (wCoeff[0] * V_t_0 + wCoeff[1] * V_t_1)

                # Save intermediate frame
                for batchIndex in range(frame0.shape[0]):
                    (self._TP(Ft_p[batchIndex].cpu().detach())).resize(self._oriDim, Image.BILINEAR).save(os.path.join(outputPath, str(frameCounter + self._sf * batchIndex) + ".jpg"))
                frameCounter += 1
            
            # Set counter accounting for batching of frames
            frameCounter += self._sf * (frame0.shape[0] - 1)


if __name__ == "__main__":
    slomo = Slomo("SuperSloMo39.ckpt", sf=128)
    slomo.process("testImages/1.jpg", "testImages/2.jpg", "slomoResult")
