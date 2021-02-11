import os
import copy
import numpy as np
import cv2
from PIL import ImageDraw


##############################################################################
class IndexArray():
    def __init__(self, index=0):
        self.index = index

    def __call__(self, input):
        return input[self.index]


class ArgMax():
    def __init__(self, axis=-1):
        self.axis = axis

    def __call__(self, tensor):
        if self.axis is None:
            axis = 1 if tensor.ndim == 4 else 0
        else:
            axis = self.axis
        #
        output = tensor.argmax(axis=axis)
        output = output[0]
        return output


class Concat():
    def __init__(self, axis=-1, start_index=0, end_index=-1):
        self.axis = axis
        self.start_index = start_index
        self.end_index = end_index

    def __call__(self, tensor_list):
        if isinstance(tensor_list, (list,tuple)):
            max_dim = 0
            for t_idx, t in enumerate(tensor_list):
                max_dim = max(max_dim, t.ndim)
            #
            for t_idx, t in enumerate(tensor_list):
                if t.ndim < max_dim:
                    tensor_list[t_idx] = t[...,np.newaxis]
                #
            #
            tensor = np.concatenate(tensor_list[self.start_index:self.end_index], axis=self.axis)
        else:
            tensor = tensor_list
        #
        return tensor


##############################################################################
class SegmentationImageResize():
    def __init__(self):
        self.image_shape = None

    def __call__(self, label):
        cv2.resize(label, dsize=(self.image_shape[1],self.image_shape[0]), interpolation=cv2.INTER_NEAREST)
        return label

    def set_info(self, info_dict):
        self.image_shape = info_dict['preprocess']['image_shape']


class SegmentationImageSave():
    def __init__(self):
        self.save_path = None
        self.colors = [(r,g,b) for r in range(0,256,32) for g in range(0,256,32) for b in range(0,256,32)]

    def __call__(self, bbox):
        img = copy.deepcopy(self.image)
        if isinstance(img, np.ndarray):
            # add fill code here
            cv2.imwrite(self.save_path, img[:,:,::-1])
        else:
            # add fill code here
            img.save(self.save_path)
        #
        return bbox

    def set_info(self, info_dict):
        image_path = info_dict['preprocess']['image_path']
        self.image = info_dict['preprocess']['image']
        image_name = os.path.split(image_path)[-1]
        work_dir = info_dict['session']['work_dir']
        save_dir = os.path.join(work_dir, 'segmentation')
        os.makedirs(save_dir, exist_ok=True)
        self.save_path = os.path.join(save_dir, image_name)


##############################################################################
class DetectionResize():
    def __init__(self):
        self.image_shape = None

    def __call__(self, bbox):
        # avoid accidental overflow
        bbox = bbox.clip(-1e6, 1e6)
        # apply scaling
        bbox[...,0] *= self.image_shape[1]
        bbox[...,1] *= self.image_shape[0]
        bbox[...,2] *= self.image_shape[1]
        bbox[...,3] *= self.image_shape[0]
        return bbox

    def set_info(self, info_dict):
        self.image_shape = info_dict['preprocess']['image_shape']


class DetectionFilter():
    def __init__(self, score_thr):
        self.score_thr = score_thr

    def __call__(self, bbox):
        if self.score_thr is not None:
            bbox_score = bbox[:,5]
            bbox_selected = bbox_score >= self.score_thr
            bbox = bbox[bbox_selected,...]
        #
        return bbox


class DetectionFormatting():
    def __init__(self, dst_indices=(0,1,2,3), src_indices=(1,0,3,2)):
        self.src_indices = src_indices
        self.dst_indices = dst_indices

    def __call__(self, bbox):
        bbox_copy = copy.deepcopy(bbox)
        bbox_copy[...,self.dst_indices] = bbox[...,self.src_indices]
        return bbox_copy


DetectionXYXY2YXYX = DetectionFormatting
DetectionYXYX2XYXY = DetectionFormatting
DetectionYXHW2XYWH = DetectionFormatting


class DetectionXYXY2XYWH():
    def __call__(self, bbox):
        w = bbox[...,2] - bbox[...,0]
        h = bbox[...,3] - bbox[...,1]
        bbox[...,2] = w
        bbox[...,3] = h
        return bbox


class DetectionXYWH2XYXY():
    def __call__(self, bbox):
        x2 = bbox[...,0] + bbox[...,2]
        y2 = bbox[...,1] + bbox[...,3]
        bbox[...,2] = x2
        bbox[...,3] = y2
        return bbox


class DetectionImageSave():
    def __init__(self):
        self.save_path = None
        self.colors = [(r,g,b) for r in range(0,256,32) for g in range(0,256,32) for b in range(0,256,32)]
        self.thickness = 2

    def __call__(self, bbox):
        img = copy.deepcopy(self.image)
        if isinstance(img, np.ndarray):
            for bbox_one in bbox:
                label = int(bbox_one[4])
                label_color = self.colors[label % len(self.colors)]
                pt1 = (int(bbox_one[0]),int(bbox_one[1]))
                pt2 = (int(bbox_one[2]),int(bbox_one[3]))
                cv2.rectangle(img, pt1, pt2, color=label_color, thickness=self.thickness)
            #
            cv2.imwrite(self.save_path, img[:,:,::-1])
        else:
            img_rect = ImageDraw.Draw(img)
            for bbox_one in bbox:
                label = int(bbox_one[4])
                label_color = self.colors[label % len(self.colors)]
                rect = (int(bbox_one[0]),int(bbox_one[1]),int(bbox_one[2]),int(bbox_one[3]))
                img_rect.rectangle(rect, outline=label_color, width=self.thickness)
            #
            img.save(self.save_path)
        #
        return bbox

    def set_info(self, info_dict):
        image_path = info_dict['preprocess']['image_path']
        self.image = info_dict['preprocess']['image']
        image_name = os.path.split(image_path)[-1]
        work_dir = info_dict['session']['work_dir']
        save_dir = os.path.join(work_dir, 'detection')
        os.makedirs(save_dir, exist_ok=True)
        self.save_path = os.path.join(save_dir, image_name)
