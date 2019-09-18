import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import re
import os

r'''
cd "C:\Users\Brian Kardon\Dropbox\Documents\Work\Cornell Lab Tech\Projects\Video VI\AVCombyne"
python AVCombyne.py
'''

def generateMergeCommand(commandTemplate='', videoPath='', audioPath='', outputPath=''):
    return commandTemplate.format(videoPath=videoPath, audioPath=audioPath, outputPath=outputPath)


class AVCombyne:
    def __init__(self, root):
        self.master = root
        self.paramFrame = ttk.Frame(self.master)
        self.matchesFrame = ttk.Frame(self.master)
        self.commandFrame = ttk.Frame(self.master)
        self.paramMatchesSeparator = ttk.Separator(self.master, orient=tk.HORIZONTAL)
        self.matchesCommandSeparator = ttk.Separator(self.master, orient=tk.HORIZONTAL)
        self.filetypes = ['video', 'audio']
        self.folderPathVars = {}
        self.folderEntries = {}
#        self.folderSelectionButtons = {}
        self.folderEntryLabels = {}
        self.fileListTextScrollbars = {}
        self.fileListTexts = {}
        self.fileListTextLabels = {}
        self.regexVars = {}
        self.regexEntries = {}
        self.regexEntryLabels = {}

        self.files = {}
        for filetype in self.filetypes:
            self.folderPathVars[filetype] = tk.StringVar()
            self.folderPathVars[filetype].trace('w', self.updateFiles)
            self.folderEntries[filetype] = ttk.Entry(self.paramFrame, textvariable=self.folderPathVars[filetype], width=100)
            self.folderEntryLabels[filetype] = ttk.Label(self.paramFrame, text='Directory to find '+filetype+' files')
#            self.folderSelectionButtons[filetype] = ttk.Button(self.paramFrame, text="Select "+filetype+" folder", command=lambda:self.selectFolder(filetype))
            self.fileListTexts[filetype] = tk.Text(self.paramFrame, height=8)
            self.fileListTextScrollbars[filetype] = ttk.Scrollbar(self.paramFrame, command=self.fileListTexts[filetype].yview)
            self.fileListTexts[filetype]['yscrollcommand'] = self.fileListTextScrollbars[filetype].set
            self.fileListTextLabels[filetype] = ttk.Label(self.paramFrame, text=filetype.capitalize() + " files found")
            self.regexVars[filetype] = tk.StringVar()
            def generateRegexChangeHandler(filetype):
                return lambda *args:self.handleRegexUpdate(filetype)
            self.regexVars[filetype].trace('w', generateRegexChangeHandler(filetype)) #updateFiles)
            self.regexEntries[filetype] = ttk.Entry(self.paramFrame, textvariable=self.regexVars[filetype], width=100)
            self.regexEntryLabels[filetype] = ttk.Label(self.paramFrame, text=filetype.capitalize()+' filename pattern (match regex subgroups)')
            self.files[filetype] = []

        self.matchesTextLabel = ttk.Label(self.matchesFrame, text="Matches")
        self.matchesText = tk.Text(self.matchesFrame, height=8, width=150)
        self.matchesScrollbar = ttk.Scrollbar(self.matchesFrame, command=self.matchesText.yview)
        self.matchesText['yscrollcommand'] = self.matchesScrollbar.set
        self.mismatchesTextLabel = ttk.Label(self.matchesFrame, text="Mismatches")
        self.mismatchesText = tk.Text(self.matchesFrame, height=8, width=150)
        self.mismatchesScrollbar = ttk.Scrollbar(self.matchesFrame, command=self.mismatchesText.yview)
        self.mismatchesText['yscrollcommand'] = self.mismatchesScrollbar.set

        self.outputFolderEntryLabel = ttk.Label(self.commandFrame, text='Directory to put merged files')
        self.outputFolderEntry = ttk.Entry(self.commandFrame, width=100)
        self.nameBaseVar = tk.StringVar()
        self.nameBaseLabel = ttk.Label(self.commandFrame, text="Select which file type to use as the base for the name of the merged file:")
        self.nameBaseButtons = {}
        for filetype in self.filetypes:
            self.nameBaseButtons[filetype] = tk.Radiobutton(self.commandFrame, variable=self.nameBaseVar, text=filetype.capitalize()+" file", value=filetype)
        self.commandTemplateEntryLabel = ttk.Label(self.commandFrame, text='Merge command template. Use {videopath}, {audioPath}, and {outputPath} as placeholders.')
        self.commandTemplateEntry = ttk.Entry(self.commandFrame, width=100)
        self.dryRunVar = tk.IntVar()
        self.dryRunButton = ttk.Checkbutton(self.commandFrame, text="Dry run", variable=self.dryRunVar)
        self.executeButton = ttk.Button(self.commandFrame, text="Execute audio/video merge", command=self.execute)

        self.matches = {}
        self.update()

        # self.folderPathVars['video'].set(r'C:\Users\Brian Kardon\Downloads\femCAF audio video matchup')
        # self.folderPathVars['audio'].set(r'C:\Users\Brian Kardon\Downloads\femCAF audio video matchup\Ch1\0373\2019_09_17')
        self.regexVars['video'].set(r'2019-([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})\.[0-9]{3}\.avi')
        self.regexVars['audio'].set(r'([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})[\.\-\_]([0-9]{2})\.wav')
        defaultCommandTemplate = 'ffmpeg -i "{videoPath}" -i "{audioPath}" -shortest "{outputPath}"'
        self.commandTemplateEntry.insert(0, defaultCommandTemplate)
        # self.outputFolderEntry.insert(0, self.folderPathVars['video'].get())
        self.nameBaseVar.set('audio')

        print("Dry run:", self.dryRunVar.get() == 1)


    # def selectFolder(self, filetype):
    #     # self.master.withdraw()
    #     path = filedialog.askdirectory(parent=self.master,
    #                                    title="Choose a folder to look for "+filetype+" files",
    #                                    initialdir='.',
    #                                    mustexist=True)
    #     self.folderEntries[filetype].delete("0.0", tk.END)
    #     self.folderEntries[filetype].insert("0.0", path)
    #     # self.master.deiconify()

    def handleRegexUpdate(self, filetype):
        regex = self.regexVars[filetype].get()
        if len(regex) == 0:
            self.regexEntries[filetype].config(background='white')
        else:
            try:
                re.compile(regex)
                self.regexEntries[filetype].config(background='light green')
            except re.error:
                self.regexEntries[filetype].config(background='pink')
        self.updateFiles()

    def updateFiles(self, *args):
        for filetype in self.filetypes:
            self.findFiles(filetype)
            self.updateFileListText(filetype)
        self.findMatches()
        self.updateMatches()
        # self.update()

    def findFiles(self, filetype):
        directory = self.folderPathVars[filetype].get()
        try:
            self.files[filetype] = os.listdir(directory)
        except FileNotFoundError:
            self.files[filetype] = []

    def updateFileListText(self, filetype):
        self.fileListTexts[filetype].delete("0.0", tk.END)
        for file in self.files[filetype]:
            self.fileListTexts[filetype].insert(tk.END, file+'\n')

    def findMatches(self):
        self.matches = {}
        for filetype in self.filetypes:
            regex = self.regexVars[filetype].get()
            try:
                re.compile(regex)
            except re.error:
                continue
            for file in self.files[filetype]:
                match = re.search(regex, file)
                if match is not None:
                    matchFields = match.groups()
                else:
                    matchFields = None
                if matchFields not in self.matches:
                    self.matches[matchFields] = dict(zip(self.filetypes, [[] for filetype  in self.filetypes]))
                self.matches[matchFields][filetype].append(file)

    def updateMatches(self):
        self.matchesText.delete("0.0", tk.END)
        self.mismatchesText.delete("0.0", tk.END)
        for filetype in self.matches:
            match = self.matches[filetype]
            if len(match['video']) == 1 and len(match['audio']) == 1:
                matchLine = match['video'][0] + ' <==> ' + match['audio'][0] + '\n'
                self.matchesText.insert(tk.END, matchLine)
            else:
                matchLine = ', '.join(match['video'] + match['audio']) + '\n'
                self.mismatchesText.insert(tk.END, matchLine)

    def execute(self):
        dryRun = (self.dryRunVar.get() == 1)
        print("Execute")
        commandTemplate = self.commandTemplateEntry.get()
        videoDir = self.folderPathVars['video'].get()
        audioDir = self.folderPathVars['audio'].get()
        outputDir = self.outputFolderEntry.get()

        commands = []

        for match in self.matches:
            if len(self.matches[match]['video']) == 1:
                videoName = self.matches[match]['video'][0]
                videoPath = os.path.join(videoDir, videoName)
            else:
                videoPath = None
            if len(self.matches[match]['audio']) == 1:
                audioName = self.matches[match]['audio'][0]
                audioPath = os.path.join(audioDir, audioName)
            else:
                audioPath = None

            if videoPath is not None and audioPath is not None:
                outputName, ext = os.path.splitext(videoName)
                outputPath = os.path.join(outputDir, outputName+'_merged.avi')
                command = generateMergeCommand(commandTemplate=commandTemplate, videoPath=videoPath, audioPath=audioPath, outputPath=outputPath)
                commands.append(command)
        for command in commands:
            print(command)
            if not dryRun:
                os.system(command)

    def update(self):
        self.paramFrame.grid(row=0)
        self.paramMatchesSeparator.grid(row=1, sticky=tk.EW, pady=5)
        self.matchesFrame.grid(row=2)
        self.matchesCommandSeparator.grid(row=3, sticky=tk.EW, pady=5)
        self.commandFrame.grid(row=4, sticky=tk.EW)

        for column, filetype in enumerate(self.filetypes):
#            self.folderSelectionButtons[filetype].grid(row=0, column=column)
            self.folderEntryLabels[filetype].grid(row=0, column=2*column, columnspan=2)
            self.folderEntries[filetype].grid(row=1, column=2*column, columnspan=2)
            self.fileListTextLabels[filetype].grid(row=2, column=2*column, columnspan=2)
            self.fileListTexts[filetype].grid(row=3, column=2*column)
            self.fileListTextScrollbars[filetype].grid(row=3, column=2*column+1, sticky=tk.N + tk.S)
            self.regexEntryLabels[filetype].grid(row=4, column=2*column, columnspan=2)
            self.regexEntries[filetype].grid(row=5, column=2*column, columnspan=2)

        self.matchesTextLabel.grid(row=0, column=0, columnspan=2)
        self.matchesText.grid(row=1, column=0)
        self.matchesScrollbar.grid(row=1, column=1, sticky=tk.N + tk.S)
        self.mismatchesTextLabel.grid(row=2, column=0, columnspan=2)
        self.mismatchesText.grid(row=3, column=0)
        self.mismatchesScrollbar.grid(row=3, column=1, sticky=tk.N + tk.S)

        self.outputFolderEntryLabel.grid(row=0, column=0, sticky=tk.W)
        self.outputFolderEntry.grid(row=0, column=1, columnspan=2, sticky=tk.EW)
        self.nameBaseLabel.grid(row=1, column=0, sticky=tk.W)
        self.nameBaseButtons['video'].grid(row=1, column=1, sticky=tk.W)
        self.nameBaseButtons['audio'].grid(row=1, column=2, sticky=tk.W)
        self.commandTemplateEntryLabel.grid(row=2, column=0, sticky=tk.W)
        self.commandTemplateEntry.grid(row=2, column=1, columnspan=2, sticky=tk.EW)
        self.executeButton.grid(row=3, column=0, sticky=tk.EW)
        self.dryRunButton.grid(row=3, column=1, sticky=tk.W)

root = tk.Tk()
avc = AVCombyne(root)
root.mainloop()
