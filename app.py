import os
import wx

from blur import blur


class FileDrop(wx.FileDropTarget):
    def __init__(self, func):
        wx.FileDropTarget.__init__(self)
        self.func = func

    def OnDropFiles(self, _x: int, _y: int, filenames: list[str]):
        for filename in filenames:
            self.func(filename)

        return True


class InputFrame(wx.Frame):
    """
    A Frame that says Hello World
    """

    def __init__(self, *args, **kw):
        super(InputFrame, self).__init__(*args, **kw)

        self.blur_queue: list[str] = []

        self.panel = wx.Panel(self)

        text = wx.StaticText(self.panel, label="Drag and drop an image to blur it")
        font = text.GetFont()
        font.PointSize += 5
        bold_font = font.Bold()
        bold_font.PointSize += 5
        text.SetFont(bold_font)

        self.ratio: tuple[float, float] = (16, 9)
        self.ratio_label = wx.StaticText(self.panel, -1, "Goal ratio: 16x9")
        self.ratio_label.SetFont(font)
        self.update_ratio_button = wx.Button(self.panel, -1, "Change ratio")
        self.update_ratio_button.SetFont(font)

        self.progressText = wx.StaticText(self.panel, label="")
        self.progressText.SetFont(font)

        self.ratio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ratio_sizer.Add(self.ratio_label, wx.SizerFlags().Border(wx.RIGHT, 20))
        self.ratio_sizer.Add(
            self.update_ratio_button, wx.SizerFlags().Border(wx.TOP, -5)
        )

        # create a sizer to manage the layout of child widgets
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.superAdd(self.sizer, text)
        self.superAdd(self.sizer, self.ratio_sizer)
        self.superAdd(self.sizer, self.progressText)
        self.panel.SetSizer(self.sizer)

        # create a drop target
        drop_target = FileDrop(self.blurImage)
        self.SetDropTarget(drop_target)

        # create a menu bar
        self.makeMenuBar()

        # bind
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdate)
        self.Bind(wx.EVT_BUTTON, self.GetRatio, self.update_ratio_button)

    def superAdd(self, sizer: wx.BoxSizer, item: wx.StaticText | wx.BoxSizer):
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        item_sizer.Add(item, wx.SizerFlags().Border(wx.LEFT, 25))
        sizer.Add(item_sizer, wx.SizerFlags().Border(wx.TOP, 10))

    def makeMenuBar(self):
        menuBar = wx.MenuBar()

        filesMenu = wx.Menu()
        filesItem = filesMenu.Append(-1, "&Browse files")

        exitMenu = wx.Menu()
        exitItem = exitMenu.Append(wx.ID_EXIT)

        menuBar.Append(filesMenu, "&Files")
        menuBar.Append(exitMenu, "&Exit")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.OnOpen, filesItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)

    def blurImage(self, filename: str):
        name = os.path.basename(filename)
        self.progressText.SetLabel(f"Bluring {name} ...")
        self.blur_queue.append(filename)

    def GetRatio(self, _event: wx.CommandEvent):
        error_message = "Valid formats: axb or a:b, where a and b are numbers."

        with wx.TextEntryDialog(
            self.panel, "Type a new ratio:", "Ratio picker", "", style=wx.OK | wx.CANCEL
        ) as entryDialog:
            while True:
                rt_id = entryDialog.ShowModal()
                if rt_id == wx.ID_CANCEL:
                    return

                value = entryDialog.GetValue()
                if value == "":
                    break

                values = []
                if ":" in value:
                    values = value.split(":")
                elif "x" in value:
                    values = value.split("x")

                if len(values) != 2:
                    entryDialog.SetValue(error_message)
                    continue

                try:
                    a, b = float(values[0]), float(values[1])
                except ValueError:
                    entryDialog.SetValue(error_message)
                    continue

                self.ratio_label.SetLabel(f"Goal ratio: {a:.6g}:{b:.6g}")
                self.ratio_sizer.Layout()
                self.sizer.Layout()
                self.ratio = (a, b)
                break

    def OnUpdate(self, _event: wx.UpdateUIEvent):
        # this is probably a hack, but such is life
        if len(self.blur_queue) > 0:
            filename = self.blur_queue.pop(0)
            name = os.path.basename(filename)
            try:
                blur(filename, self.ratio)
                self.progressText.SetLabel(f"Bluring {name} ...\nDone!")
            except ValueError as err:
                error_type = str(type(err))[8:-2]
                self.progressText.SetLabel(
                    f"Bluring {name} ...\n{error_type} occured: {err}"
                )
            self.sizer.Layout()

    def OnOpen(self, _event: wx.CommandEvent):
        # ask the user what new file to open
        wildcard = "Images (*.jpg,*.jpeg,*.png)|*.jpg;*.jpeg;*.png|All (*.*)|*.*"
        with wx.FileDialog(
            self,
            "Open image file",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.blurImage(pathname)
            except IOError:
                wx.LogError(f"Cannot open file '{pathname}'.")

    def OnExit(self, _event: wx.CommandEvent):
        """Close the frame, terminating the application."""
        self.Close(True)


if __name__ == "__main__":
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = InputFrame(None, title="Blurinator", size=(640, 360))
    frm.Show()
    app.MainLoop()
