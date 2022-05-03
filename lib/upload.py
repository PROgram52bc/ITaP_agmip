from ipywidgets import FileUpload, Dropdown, Button, VBox, HBox
from traitlets import Unicode
from .prop import ComputedProp, SyncedProp, Prop, conditional_widget, displayable
from .utils import get_dir_content
import os

DEBUG=1

def D(msg):
    if DEBUG:
        print(msg)

class Upload(VBox):
    def __init__(self, upload_dir=".", upload_fname=None, overwrite=False):
        """ upload_fname will be the name of the uploaded file, if None, use the original file name """
        self._fu = FileUpload()
        self._clear_btn = Button(description="Clear")
        self._confirm_btn = Button(description="Confirm")
        super().__init__(children=[self._fu, self._clear_btn, self._confirm_btn])

        self._upload_dir = upload_dir
        self._upload_fname = upload_fname
        self._overwrite = overwrite

        self._clear_btn.on_click(lambda _: self._clear_pending_file())
        self._confirm_btn.on_click(lambda _: self._confirm_upload())
        self._has_pending_file = ComputedProp(use_none=True) << (self._fu, dict(name='v', sync=True)) >> (lambda v: bool(v))
        self._last_uploaded_file = None
        self._upload_cb = lambda _: None
        self._error_cb = lambda _: None
        SyncedProp() << ~self._has_pending_file >> (self._clear_btn, dict(prop='disabled')) >> (self._confirm_btn, dict(prop='disabled'))
        SyncedProp() << self._has_pending_file >> (self._fu, dict(prop='disabled'))

    def _handle_error(self, msg="Error encountered uploading file"):
        if self._error_cb is not None:
            self._error_cb({'message': msg})
        D(msg)

    def _confirm_upload(self):
        D("confirm called")
        os.makedirs(self._upload_dir, exist_ok=True)
        uploaded = next(iter(self._fu.value.values()), None)
        if uploaded is None:
            self._handle_error("Nothing to upload")
            return
        fname = uploaded['metadata']['name'] if self._upload_fname is None else upload_fname
        lmod = uploaded['metadata']['lastModified']/1000 # accomondate the value given by ipywidgets.FileUpload
        dest_path = os.path.join(self._upload_dir, fname)
        D(f"fname: {fname}")
        D(f"lmod: {lmod}")
        D(f"dest_path: {dest_path}")
        if not self._overwrite and os.path.exists(dest_path):
            self._handle_error("File exists, not overwriting")
            return
        with open(dest_path, "wb") as f:
            f.write(uploaded['content'])
        os.utime(dest_path, (lmod, lmod))
        self._last_uploaded_file = dest_path # is this needed? use callback exclusively?
        self._clear_pending_file()
        if self._upload_cb is not None:
            self._upload_cb({'path': dest_path})

    def _clear_pending_file(self):
        self._fu._counter = 0
        self._fu.set_trait('value', {})

    # def _ipython_display_(self):
    #     display(self._fu)
    #     display(self._clear_btn)
    #     display(self._confirm_btn)

    def on_upload(self, cb):
        """ cb accepts a dictionary with key 'path', pointing to the full path of the uploaded file """
        assert callable(cb)
        self._upload_cb = cb

    def on_error(self, cb):
        """ cb accepts a dictionary with key 'message', indicating the error message """
        assert callable(cb)
        self._error_cb = cb


class SelectOrUpload(VBox):
    def __init__(self, select_dir=".", upload_dir=".", upload_fname=None, overwrite=False):
        """ upload_fname will be the name of the uploaded file, if None, use the original file name """
        # assume content is static
        self._select = Dropdown(options=get_dir_content(select_dir))
        self._upload = Upload(upload_dir=upload_dir, upload_fname=upload_fname, overwrite=overwrite)

        # whether to use the uploaded file or the selected file
        self.use_upload = Prop(value=False)
        self.uploaded_file = None

        self.target_file = ComputedProp() \
            << (self.use_upload, dict(name='up')) \
            << self._select \
            >> (lambda up: self.uploaded_file if up else self._select.value)

        # button to switch back to selection mode
        self._use_select_btn = Button(description="Use Existing Files")
        self._use_select_btn.on_click(self._cb_use_upload_false)

        super().__init__(children=[
            displayable(self.target_file, "Selected"),
            conditional_widget(self.use_upload,
                               self._use_select_btn,
                               self._select),
            self._upload])

        self._upload.on_upload(self._cb_use_upload_true)

    def _cb_use_upload_true(self, payload):
        self.uploaded_file = payload['path']
        self.use_upload.value = True

    def _cb_use_upload_false(self, _):
        self.uploaded_file = None
        self.use_upload.value = False
