from jacinto_ai_benchmark import preprocess, postprocess, constants
from jacinto_ai_benchmark.defaults import *


############################################################
# common settings
num_frames = 10000 #50000
max_frames_calib = 100
max_calib_iterations = 50
modelzoo_path = '../jacinto-ai-modelzoo/models'
datasets_path = f'./dependencies/datasets'
cuda_devices = [0,1,2,3,0,1,2,3] #None
tidl_dir = './dependencies/c7x-mma-tidl'
tidl_tensor_bits = 32 #8 #16 #32


############################################################
# quantization params & session config
quantization_params = QuantizationParams(tidl_tensor_bits, max_frames_calib, max_calib_iterations)
session_tvm_dlr_cfg = quantization_params.get_session_tvm_dlr_cfg()
session_tflite_rt_cfg = quantization_params.get_session_tflite_rt_cfg()


quantization_params_qat = QuantizationParams('qat', max_frames_calib, max_calib_iterations)
session_tvm_dlr_cfg_qat = quantization_params_qat.get_session_tvm_dlr_cfg()
session_tflite_rt_cfg_qat = quantization_params_qat.get_session_tflite_rt_cfg()


############################################################
# dataset settings
imagenet_train_cfg = dict(
    path=f'{datasets_path}/imagenet/train',
    split=f'{datasets_path}/imagenet/train.txt',
    shuffle=True,num_frames=quantization_params.get_num_frames_calib())
imagenet_val_cfg = dict(
    path=f'{datasets_path}/imagenet/val',
    split=f'{datasets_path}/imagenet/val.txt',
    shuffle=True,num_frames=num_frames)


