import os
from jacinto_ai_benchmark import *

import benchmark_detection_helper as det_helper

# the cwd must be the root of the respository
if os.path.split(os.getcwd())[-1] == 'scripts':
    os.chdir('../')
#
# make sure current directory is visible for python import
if not os.environ['PYTHONPATH'].startswith(':'):
    os.environ['PYTHONPATH'] = ':' + os.environ['PYTHONPATH']
#

import config_settings as config
work_dir = os.path.join('./work_dirs', os.path.splitext(os.path.basename(__file__))[0], f'{config.tidl_tensor_bits}bits')
print(f'work_dir = {work_dir}')


################################################################################################
# configs for each model pipeline
common_cfg = {
    'type':'accuracy',
    'run_import':config.run_import,
    'run_inference':config.run_inference,
    'calibration_dataset':datasets.COCODetection(**config.coco_det_train_cfg),
    'input_dataset':datasets.COCODetection(**config.coco_det_val_cfg),
}

postproc_detection_onnx = config.get_postproc_detection_onnx(score_thr=config.detection_thr, save_detections=config.detection_save)
postproc_detection_tflite = config.get_postproc_detection_tflite(score_thr=config.detection_thr, save_detections=config.detection_save)

pipeline_configs = [
    #################################################################
    #       TFLITE MODELS
    #################mlperf models##############################
    # mlperf edge: detection - ssd_mobilenet_v1_coco_2018_01_28 expected_metric: 23.0% ap[0.5:0.95] accuracy
    utils.dict_update(common_cfg, {
        'preprocess':config.get_preproc_inception((300,300), (300,300), backend='cv2'),
        'session':sessions.TFLiteRTSession(**config.session_tflite_rt_cfg, work_dir=work_dir,
            model_path=f'{config.modelzoo_path}/vision/detection/coco/mlperf/ssd_mobilenet_v1_coco_2018_01_28.tflite'),
        'postprocess': postproc_detection_tflite,
        'metric':dict(label_offset_pred=det_helper.coco_label_offset_90to90())
    }),
    # mlperf mobile: detection - ssd_mobilenet_v2_coco_300x300 - expected_metric: 22.0% COCO AP[0.5-0.95]
    utils.dict_update(common_cfg, {
        'preprocess':config.get_preproc_inception((300,300), (300,300), backend='cv2'),
        'session':sessions.TFLiteRTSession(**config.session_tflite_rt_cfg, work_dir=work_dir,
            model_path=f'{config.modelzoo_path}/vision/detection/coco/mlperf/ssd_mobilenet_v2_300_float.tflite'),
        'postprocess': postproc_detection_tflite,
        'metric':dict(label_offset_pred=det_helper.coco_label_offset_90to90())
    }),
    # # mlperf edge: detection - coco_ssd-resnet34_1200x1200 - expected_metric: 20.0% COCO AP[0.5-0.95]
    # utils.dict_update(common_cfg, {
    #     'preprocess':config.get_preproc_inception((1200,1200), (1200,1200), backend='cv2'),
    #     'session':sessions.TVMDLRSession(**config.session_tflite_rt_cfg, work_dir=work_dir,
    #         model_path=f'{config.modelzoo_path}/vision/detection/coco/mlperf/ssd_resnet34-ssd1200.onnx'),
    #     'postprocess': postproc_detection_tflite,
    #     'metric':dict(label_offset_pred=det_helper.coco_label_offset_80to90())
    # }),
]


################################################################################################
# execute each model
if __name__ == '__main__':
    if config.run_import or config.run_inference:
        pipelines.run(pipeline_configs, devices=config.cuda_devices)
    #
    results = pipelines.collect_results(work_dir)
    print(*results, sep='\n')

