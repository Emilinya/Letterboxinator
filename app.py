import wx
import platform
from blur import blur

FOLDER_SEPERATOR = "\\" if platform.system() == "Windows" else "/"


class FileDrop(wx.FileDropTarget):
    def __init__(self, func):
        wx.FileDropTarget.__init__(self)
        self.func = func

    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            self.func(filename)

        return True


class InputFrame(wx.Frame):
    """
    A Frame that says Hello World
    """

    def __init__(self, *args, **kw):
        super(InputFrame, self).__init__(*args, **kw)

        self.blur_queue = []

        self.panel = wx.Panel(self)

        text = wx.StaticText(
            self.panel, label="Drag and drop an image to blur it"
        )
        font = text.GetFont()
        font.PointSize += 5
        bold_font = font.Bold()
        bold_font.PointSize += 5
        text.SetFont(bold_font)

        self.ratio = (16, 9)
        self.ratio_label = wx.StaticText(self.panel, -1, "Goal ratio: 16x9")
        self.ratio_label.SetFont(font)
        self.update_ratio_button = wx.Button(self.panel, -1, "Change ratio")
        self.update_ratio_button.SetFont(font)

        self.progressText = wx.StaticText(self.panel, label="")
        self.progressText.SetFont(font)

        self.ratio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ratio_sizer.Add(
            self.ratio_label, wx.SizerFlags().Border(wx.RIGHT, 20)
        )
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

    def superAdd(self, sizer, item):
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        item_sizer.Add(item, wx.SizerFlags().Border(wx.LEFT, 25))
        sizer.Add(item_sizer, wx.SizerFlags().Border(wx.TOP, 10))

    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

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

    def blurImage(self, filename):
        name = filename.split(FOLDER_SEPERATOR)[-1]
        self.progressText.SetLabel(f"Bluring {name} ...")
        self.blur_queue.append(filename)

    def GetRatio(self, event):
        with wx.TextEntryDialog(self.panel, 'Type a new ratio:', "Ratio picker", "", style=wx.OK | wx.CANCEL) as entryDialog:
            while True:
                rt_id = entryDialog.ShowModal()
                if rt_id == wx.ID_CANCEL:
                    return

                value = entryDialog.GetValue()
                if value == "":
                    break
                try:
                    if ":" in value:
                        a, b = value.split(":")
                    elif "x" in value:
                        a, b = value.split("x")
                    a, b = float(a), float(b)
                    self.ratio_label.SetLabel(f"Goal ratio: {a:.20g}:{b:.20g}")
                    self.ratio_sizer.Layout()
                    self.sizer.Layout()
                    self.ratio = (a, b)
                    break
                except:
                    entryDialog.SetValue("valid formats: axb and a:b, where a,b are numbers")
                    continue

    def OnUpdate(self, event):
        # this is probably a hack, but such is life
        if len(self.blur_queue) > 0:
            filename = self.blur_queue.pop(0)
            name = filename.split(FOLDER_SEPERATOR)[-1]
            try:
                blur(filename, self.ratio)
                self.progressText.SetLabel(f"Bluring {name} ...\nDone!")
            except Exception as err:
                error_type = str(type(err))[8:-2]
                self.progressText.SetLabel(f"Bluring {name} ...\n{error_type} occured: {err}")
            self.sizer.Layout()

    def OnOpen(self, event):
        # ask the user what new file to open
        wildcard = "Images (*.jpg,*.jpeg,*.png)|*.jpg;*.jpeg;*.png|All (*.*)|*.*"
        with wx.FileDialog(self, "Open image file", wildcard=wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.blurImage(pathname)
            except IOError:
                wx.LogError("Cannot open file '%s'." % pathname)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = InputFrame(None, title='Blurinator', size=(640, 360))
    frm.Show()
    app.MainLoop()
