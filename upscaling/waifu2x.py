import os
import subprocess
import tempfile
from sys import platform
from typing import List
from PIL import Image
import shutil

from .common import OfflineUpscaler

if platform == 'win32':
    waifu2x_base_folder = 'waifu2x-win'
    waifu2x_executable_path = f'{waifu2x_base_folder}/waifu2x-ncnn-vulkan.exe'
    model_mapping = {
        'waifu2x-win': {
            'url': 'https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-windows.zip',
            'hash': '3f60ba0b26763c602cb75178c2051bf0c46f3cc9d13975a052a902773988a34b',
            'archive-files': {
                'waifu2x-ncnn-vulkan-20220728-windows': waifu2x_base_folder,
            },
        },
    }
elif platform == 'darwin':
    waifu2x_base_folder = 'waifu2x-macos'
    waifu2x_executable_path = f'{waifu2x_base_folder}/waifu2x-ncnn-vulkan'
    model_mapping = {
        'waifu2x-macos': {
            'url': 'https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-macos.zip',
            'hash': '9801839aa1a73a3a22e86d05f09a9b7412c289d1a03215e1b2713cc969690ba4',
            'archive-files': {
                'waifu2x-ncnn-vulkan-20220728-macos': waifu2x_base_folder,
            },
        },
    }
else:
    waifu2x_base_folder = 'waifu2x-linux'
    waifu2x_executable_path = f'{waifu2x_base_folder}/waifu2x-ncnn-vulkan'
    model_mapping = {
        'waifu2x-linux': {
            'url': 'https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-ubuntu.zip',
            'hash': 'f2244412aeaf474d58e262f636737abca24ee24cd632d86eb8f0a4c4f9649aaa',
            'archive-files': {
                'waifu2x-ncnn-vulkan-20220728-ubuntu': waifu2x_base_folder,
            },
        },
    }

class Waifu2xUpscaler(OfflineUpscaler): # ~2GB of vram
    _MODEL_MAPPING = model_mapping
    _VALID_UPSCALE_RATIOS = [1, 2, 4, 8, 16, 32]

    async def _load(self, device: str):
        pass

    async def _unload(self):
        pass

    async def _forward(self, image_batch: List[Image.Image], upscale_ratio: float) -> List[Image.Image]:
        # Has to cache images because chosen upscaler doesn't support other methods
        in_dir = tempfile.mkdtemp()
        out_dir = tempfile.mkdtemp()
        for i, image in enumerate(image_batch):
            image.save(os.path.join(in_dir, f'{i}.png'))
        self._run_waifu2x_executable(in_dir, out_dir, upscale_ratio, 0)

        output_batch = []
        for i, image in enumerate(image_batch):
            img_path = os.path.join(out_dir, f'{i}.png')
            if os.path.exists(img_path):
                output_batch.append(Image.open(img_path))
            else:
                output_batch.append(image)

        shutil.rmtree(in_dir)
        shutil.rmtree(out_dir)
        return output_batch

    def _run_waifu2x_executable(self, image_directory: str, output_directory: str, upscale_ratio: float, denoise_level: int):
        cmds = []
        cmds.append(self._get_file_path(waifu2x_executable_path))
        cmds.append('-i')
        cmds.append(image_directory)
        cmds.append('-o')
        cmds.append(output_directory)
        cmds.append('-m')
        cmds.append(os.path.join(self._get_file_path(waifu2x_base_folder), 'models-cunet'))
        cmds.append('-n')
        cmds.append(str(denoise_level))
        cmds.append('-s')
        cmds.append(str(upscale_ratio))
        subprocess.check_call(cmds)
