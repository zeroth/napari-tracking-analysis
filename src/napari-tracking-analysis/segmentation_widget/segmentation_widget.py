from pathlib import Path
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox
from qtpy.QtWidgets import QGridLayout
from napari_tracking_analysis.base.widget import NLayerWidget
from napari_tracking_analysis.base import AppState
from magicgui.widgets import FileEdit
from magicgui.types import FileDialogMode
import warnings
from apoc import PixelClassifier, PredefinedFeatureSet
import apoc
from napari.utils import progress
import numpy as np
from napari.utils import notifications
from qtpy import uic
import napari_tracking_analysis.utils as utils


class FileEditWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(QLabel("Classifier file"))
        self.filename_edit = FileEdit(
            mode=FileDialogMode.OPTIONAL_FILE,
            filter='*.cl',
            value="Classifier.cl")
        self.layout().addWidget(self.filename_edit.native)

    def value(self):
        return self.filename_edit.value.absolute()


class FeatureSelector(QWidget):
    def __init__(self, parent, feature_definition: str = PredefinedFeatureSet.small_dog_log.value):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(2)
        self.feature_definition = " " + feature_definition.lower() + " "

        self.available_features = [
            "gaussian_blur", "difference_of_gaussian", "laplace_box_of_gaussian_blur"]
        self.available_features_short_names = ["Gauss", "DoG", "LoG", "SoG"]
        self.available_features_tool_tips = [
            "Gaussian filter", "Difference of Gaussian", "Laplacian of Gaussian"]

        self.radii = [0.3, 0.5, 1, 2, 3, 4, 5, 10, 15, 25]

        # Headline
        table = QWidget()
        table.setLayout(QGridLayout())
        table.layout().setContentsMargins(0, 0, 0, 0)
        table.layout().setSpacing(2)
        label_sigma = QLabel("sigma")
        sigma_help = "Increase sigma in case a pixels classification depends \
            on the intensity of other more proximal pixels."
        label_sigma.setToolTip(sigma_help)
        table.layout().addWidget(label_sigma, 0, 0)

        for i, r in enumerate(self.radii):
            label_sigma = QLabel(str(r))
            label_sigma.setToolTip(sigma_help)
            table.layout().addWidget(label_sigma, 0, i + 1)

        # Feature lines
        row = 1
        for f, f_short, f_tooltip in zip(self.available_features, self.available_features_short_names,
                                         self.available_features_tool_tips):
            label = QLabel(f_short)
            label.setToolTip(f_tooltip)
            table.layout().addWidget(label, row, 0)
            for i, r in enumerate(self.radii):
                table.layout().addWidget(
                    self._make_checkbox("", f + "=" + str(r),
                                        (f + "=" + str(r)) in self.feature_definition),
                    row, i + 1)
            row = row + 1

        self.layout().addWidget(table)

        self.layout().addWidget(self._make_checkbox("Consider original image as well",
                                                    "original", " original " in self.feature_definition))

    def _make_checkbox(self, title, feature, checked):
        checkbox = QCheckBox(title)
        checkbox.setChecked(checked)

        def check_the_box(*args, **kwargs):
            if checkbox.isChecked():
                self._add_feature(feature)
            else:
                self._remove_feature(feature)

        checkbox.stateChanged.connect(check_the_box)
        return checkbox

    def _remove_feature(self, feature):
        self.feature_definition = " " + \
            (self.feature_definition.replace(" " + feature + " ", " ")).strip() + " "
        print(self.feature_definition)

    def _add_feature(self, feature):
        print("adding: " + feature)
        self.feature_definition = self.feature_definition + " " + feature + " "
        print(self.feature_definition)

    def getFeatures(self):
        return self.feature_definition.replace("  ", " ").strip(" ")


class _segmentation_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'segmentation_widget.ui')
        self.load_ui(UI_FILE)
        self.numMaxDepthSpinner.setMinimum(2)
        self.numMaxDepthSpinner.setMaximum(10)
        self.numMaxDepthSpinner.setValue(2)
        self.numMaxDepthSpinner.setToolTip("The more image channels and features you selected, \
                                         the higher the maximum tree depth should be to retrieve \
                                         a reliable and robust classifier. \
                                         The deeper the trees, the longer processing will take.")

        self.numTreesSpinner.setMinimum(1)
        self.numTreesSpinner.setMaximum(1000)
        self.numTreesSpinner.setValue(100)
        self.numTreesSpinner.setToolTip("The more image channels and features you selected, \
                                     the more trees should be used to retrieve a reliable and robust classifier. \
                                     The more trees, the longer processing will take.")

        self.chkRemoveSmallObj.setChecked(True)
        self.chkRemoveSmallObj.stateChanged.connect(self.minObjSizeSpinner.setEnabled)
        self.minObjSizeSpinner.setMinimum(0)
        self.minObjSizeSpinner.setValue(6)

    def load_ui(self, path):
        uic.loadUi(path, self)


class _walking_average_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'walking_average.ui')
        self.load_ui(UI_FILE)
        self.windowSizeSpinner.setMinimum(1)
        self.windowSizeSpinner.setValue(4)
        # Blob_Log
        self.minSigmaSpinner.setMinimum(1.0)
        self.minSigmaSpinner.setValue(1.0)
        self.maxSigmaSpinner.setMinimum(1.0)
        self.maxSigmaSpinner.setValue(2.0)
        self.numSigmaSpinner.setMinimum(1)
        self.numSigmaSpinner.setValue(10)
        self.thresholdSpinner.setMinimum(0.0)
        self.thresholdSpinner.setValue(0.1)
        self.overlapSpinner.setMinimum(0.0)
        self.overlapSpinner.setValue(0.5)

    def load_ui(self, path):
        uic.loadUi(path, self)


class SegmentationWidget(NLayerWidget):
    def __init__(self, app_state: AppState = None, parent=None):
        super().__init__(app_state=app_state, parent=parent)
        self.name = "Segmentation"
        self.classifier_class = PixelClassifier
        self.current_annotation = None
        self.ui = _segmentation_ui(self)
        self.avg_ui = _walking_average_ui(self)
        self.layout().addWidget(self.avg_ui)
        self.layout().addWidget(self.ui)
        # self.layout().setContentsMargins(0, 0, 0, 0)

        # walking average button
        def roalling_average_clicked(*arg, **kwargs):
            if self.get_current_image() is None:
                warnings.warn("Please select image!")
                notifications.show_warning(
                    "Please select image!")
                return

            self.walking_average(
                self.get_current_image(),
                self.avg_ui.windowSizeSpinner.value()
            )

        self.avg_ui.btnAvg.clicked.connect(roalling_average_clicked)

        # quick segment button
        def quick_segment_clicked(*arg, **kwargs):
            if self.get_current_image() is None:
                warnings.warn("Please select image!")
                notifications.show_warning(
                    "Please select image!")
                return

            label_layer = self.get_current_label()
            self.quick_segment_2d(
                image_layer=self.get_current_image(),
                label_layer=label_layer,
                min_sigma=self.avg_ui.minSigmaSpinner.value(),
                max_sigma=self.avg_ui.maxSigmaSpinner.value(),
                num_sigma=self.avg_ui.numSigmaSpinner.value(),
                threshold=self.avg_ui.thresholdSpinner.value(),
                overlap=self.avg_ui.overlapSpinner.value()
            )

        self.avg_ui.btnLog.clicked.connect(quick_segment_clicked)

        # Train button

        def train_clicked(*arg, **kwargs):
            if self.get_current_label() is None:
                warnings.warn("No ground truth annotation selected!")
                notifications.show_warning(
                    "No ground truth annotation selected!")
                return

            # if not self.check_image_sizes():
            #     warnings.warn(
            #         "Selected images and annotation must have the same dimensionality and size!")
            #     return

            if len(self.get_current_image_data()) == 0:
                warnings.warn("Please select image/channel[s] to train on.")
                return

            first_image_layer = self.get_current_image()

            self.train(
                self.get_current_image_data(),
                self.get_current_label_data(),
                self.ui.featureSelector.getFeatures(),
                self.ui.numMaxDepthSpinner.value(),
                self.ui.numTreesSpinner.value(),
                str(self.ui.filenameEdit.value()).replace("\\", "/").replace("//", "/"),
                first_image_layer.scale,
                self.ui.minObjSizeSpinner.value() if self.ui.chkRemoveSmallObj.isChecked() else None
            )
            self.state.setParameter(f"{self.name}_classifier_file",
                                    str(self.ui.filenameEdit.value()).replace("\\", "/").replace("//", "/"))

        self.ui.btnTrain.clicked.connect(train_clicked)

        # Predict button

        def predict_clicked(*arg, **kwargs):
            filename = str(self.ui.filenameEdit.value()).replace(
                "\\", "/").replace("//", "/")
            first_image_layer = self.get_current_image()

            self.predict(
                self.get_current_image_data(),
                filename,
                first_image_layer.scale
            )

        self.ui.btnSegment.clicked.connect(predict_clicked)

    def get_current_image(self):
        return self.get_layer("Image")

    def get_current_image_data(self):
        return None if self.get_current_image() is None else self.get_current_image().data

    def get_current_label(self):
        return self.get_layer('Label')

    def get_current_label_data(self):
        return None if self.get_current_label() is None else self.get_current_label().data

    def check_image_sizes(self):
        image = self.get_current_image_data()
        mask = self.get_current_label_data()
        if (image is None) or (mask is None):
            return False
        return np.array_equal(image.shape, mask.shape)

    def train(self, images, annotation, feature_definition, num_max_depth, num_trees, filename, scale=None,
              min_obj_size=None):
        print("train " + str(self.classifier_class.__name__))
        print("num images", len(images.shape))
        print("features", feature_definition)
        print("depth", num_max_depth)
        print("num trees", num_trees)
        print("file", filename)
        if len(images) == 0:
            warnings.warn("No image[s] selected")
            return

        if annotation is None:
            warnings.warn("No ground truth / annotation selected")
            return

        if len(images) == 1:
            images = images[0]

        apoc.erase_classifier(filename)
        classifier = self.classifier_class(
            opencl_filename=filename,
            num_ensembles=num_trees,
            max_depth=num_max_depth)

        print("annotation shape", annotation.shape)
        notifications.show_info(
            f"Training {str(self.classifier_class.__name__)}")

        # reduce the data size
        _ann_ind = np.argwhere(annotation >= 1)
        _ann_ind = np.unique(_ann_ind[:, 0])
        _ann_ind = _ann_ind.tolist()
        _annotation = annotation[_ann_ind]
        _images = images[_ann_ind]
        print(_annotation.shape)
        print(_images.shape)
        classifier.train(feature_definition, _annotation, _images)

        print("Training done. Applying model...")
        notifications.show_info("Training done. Applying model...")
        self.predict(images=images, filename=filename, scale=scale, min_obj_size=min_obj_size)

    def predict(self, images, filename, scale, min_obj_size=None):
        print("predict")
        print("num images", len(images))
        print("file", filename)
        import pyclesperanto_prototype as cle

        if len(images) == 0:
            warnings.warn("No image[s] selected")
            return

        if len(images) == 1:
            images = images[0]

        clf = self.classifier_class(opencl_filename=filename)
        result = np.zeros(images.shape, dtype=np.uint16)
        
        min_obj_size_gradiant = np.ceil(
            np.linspace(min_obj_size, 1, images.shape[0])).astype(
            np.uint16) if min_obj_size is not None else None
        
        if len(images.shape) >= 3:
            for i in progress(range(images.shape[0]), desc="Predicting..."):
                result[i] = np.asarray(
                    cle.equal_constant(clf.predict(image=images[i]),
                                       constant=2)) if min_obj_size is None else utils.remove_small_objects(
                    np.asarray(cle.equal_constant(clf.predict(image=images[i]), constant=2)),
                    min_size=min_obj_size_gradiant[i])
                # print(result[i])
                # np.asarray(clf.predict(image=images[i]))
        else:
            result = np.asarray(
                cle.equal_constant(clf.predict(image=images),
                                   constant=2)) if min_obj_size is None else utils.remove_small_objects(
                np.asarray(cle.equal_constant(clf.predict(image=images),
                                              constant=2)),
                min_size=min_obj_size)

        print("Applying / prediction done.")
        notifications.show_info("Applying / prediction done.")
        # import pyclesperanto_prototype as cle
        # result = cle.equal_constant(result, constant=2)

        short_filename = filename.split("/")[-1]

        _add_to_viewer(self.state.viewer, False, "Result of " +
                       short_filename, result, scale)

    def walking_average(self, image_layer, window: int = 4):
        image = image_layer.data
        ret = np.cumsum(image, axis=0, dtype=image.dtype)
        ret[window:] = ret[window:] - ret[:-window]
        ret = ret[window - 1:] / window
        _add_to_viewer(self.state.viewer, True, f"{image_layer.name}_Walking_Avg_{window}", ret, image_layer.scale)

    def quick_segment_2d(self, image_layer, label_layer, min_sigma: float = 1.0, max_sigma: float = 2.0,
                         num_sigma: int = 10, threshold: float = 0.1, overlap: float = 0.5):
        from skimage.feature import blob_log
        from skimage.exposure import rescale_intensity

        if self.state.viewer.dims.ndisplay != 2:
            warnings.warn("Plese sqitch to 2d Display Mode!")
            notifications.show_warning(
                "Plese sqitch to 2d Display Mode!")
            return
        image = image_layer.data[self.state.viewer.dims.current_step[0]]
        if label_layer is not None:
            label = label_layer.data[self.state.viewer.dims.current_step[0]]
        else:
            label_layer = self.state.viewer.add_labels(
                np.zeros(image_layer.data.shape, dtype=np.uint8),
                name="Annotation_Label")
            label = label_layer.data[self.state.viewer.dims.current_step[0]]

        im_range = np.min(image), np.max(image)
        image = rescale_intensity(image, in_range=im_range, out_range=(0, 1))
        blobs_log = blob_log(image, min_sigma=min_sigma, max_sigma=max_sigma,
                             num_sigma=num_sigma, threshold=threshold, overlap=overlap)
        print(blobs_log)
        print(f"Current pointer : {self.state.viewer.dims.current_step[0]}")
        label = utils.draw_points(label, blobs_log, fill_value=2, outline_value=1)
        # self.state.viewer.layers['Annotation_Label'].data[self.state.viewer.dims.current_step[0]] = label
        label_layer.data[self.state.viewer.dims.current_step[0]] = label
        self.state.viewer.reset_view()


def _add_to_viewer(viewer, as_image, name, data, scale=None):
    try:
        viewer.layers[name].data = data.astype(int)
        viewer.layers[name].visible = True
    except KeyError:
        if as_image:
            viewer.add_image(data, name=name, scale=scale)
        else:
            viewer.add_labels(data.astype(int), name=name, scale=scale)
