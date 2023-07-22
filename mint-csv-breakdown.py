import csv
import pandas as pd
from tabulate import tabulate
import PySimpleGUI as sg
import os

# Constants
CardPrefixes = ["Debit Purchase -visa Card 4845", "Debit Purchase Card 4845"]
INITIAL_CSV = "transactions (8).csv"
CSV_DIR = r"C:\Users\kmita\Downloads\\"
InfoPanelFont = ("Arial", 20)


# End Constants


# Helper functions
def prntTab(data):
    print(tabulate(data, headers='keys', tablefmt='psql'))


def sumValidDebits(data):
    return round(data.loc[(data['Transaction Type'] == 'debit') & (data['Ignore'] == False)]["Amount"].sum(), 2)


def sumValidCredits(data):
    pass


def getColorsForIgnored(data):
    return [(idx, "salmon" if x else "grey") for idx, x in enumerate(data["Ignore"])]


def getColorsForCategory(data, category):
    # return [(idx, mapColor(x)) for idx, x in enumerate(data["Category"])]
    return [(idx, mapColor(curCat, category, data.at[idx, "Ignore"])) for idx, curCat in enumerate(data["Category"])]


def mapColor(curCat, selectedCat, ignoreForSumming):
    if curCat == selectedCat:
        if ignoreForSumming:
            return "MediumOrchid"
        else:
            return "MediumSlateBlue"
    else:
        return "grey"


def getColWidths(data):
    return list(map(lambda x: len(str(x)), list(data.iloc[1])))


def getDirCsvNames():
    return list(filter(lambda f: ".csv" in f, os.listdir(CSV_DIR)))


def getCSVDateRange():
    return f'Dates: {instance.df["Date"].min()}-{instance.df["Date"].max()}'


# END helper functions

class Main:
    def __init__(self, csv_path):
        # Main code
        self.df = pd.read_csv(CSV_DIR + csv_path)
        print(f"Total Transactions: {len(self.df)}")

        # make transactions more readable
        for cPrefix in CardPrefixes:
            self.df["Description"] = self.df["Description"].apply(lambda x: x.replace(cPrefix, ""))

        # get rid of unneeded cols
        self.df = self.df.drop("Original Description", axis=1)
        self.df = self.df.drop("Account Name", axis=1)
        self.df = self.df.drop("Labels", axis=1)
        self.df = self.df.drop("Notes", axis=1)

        # flag potential transfers
        self.df["Ignore"] = (
            # flag anything with keywords that scream this is a tr
            (
                    self.df["Description"].str.lower().str.contains("Payment") | \
                    self.df["Description"].str.lower().str.contains("payment") | \
                    self.df["Description"].str.contains("Web Authorized") | \
                    self.df["Description"].str.contains("Transfer")
            )
        )

        # set up all categories list
        self.df_cat = self.df.groupby(['Category'])['Amount'].sum().reset_index()
        self.df_cat = self.df_cat.sort_values(by=['Amount']).reset_index()

        
        sg.Table(values=getDirCsvNames(),
                 key="FileList",
                 headings=["hello"],
                 auto_size_columns=True,
                 enable_events=True,
                 font=("Arial", 14)
                 )

        prntTab(self.df_cat)


# #######################
# ######## UI ###########
# #######################

instance = Main(INITIAL_CSV)


def getTransTable():
    return sg.Table(values=[], headings=list(instance.df.head()),
                    auto_size_columns=False,
                    enable_events=True,
                    key='transTable',
                    col_widths=getColWidths(instance.df),
                    row_colors=getColorsForIgnored(instance.df),
                    size=(7, 30),
                    font=("Arial", 14)
                    )


def getCategoryTable():
    return sg.Table(values=[], headings=list(instance.df_cat.head()),
                    auto_size_columns=True,
                    enable_events=True,
                    key='AllCategories',
                    size=(7, 7),
                    font=("Arial", 14)
                    )


def getDirectoryTable():
    return sg.Table(values=getDirCsvNames(), headings=list(instance.df_cat.head()),
                    auto_size_columns=True,
                    enable_events=True,
                    key='AllCategories',
                    size=(7, 7),
                    font=("Arial", 14)
                    )
    # return instance.fileDirDF # what?


def getLeftPanel():
    return [[getTransTable()],
            [sg.Text(f"TotalSpent: ${sumValidDebits(instance.df)}  ", key="TotalSpent", font=InfoPanelFont),
             sg.Text(getCSVDateRange(), font=InfoPanelFont, key="DateRange")],
            ]


def getRightPanel():
    return [
        [getDirectoryTable()],
        [sg.Button("Read File", size=(25, 2), key="OK")],
        [getCategoryTable()]
    ]


layout = [
    [sg.Column(getLeftPanel(), key="leftCol"),
     sg.Column(getRightPanel(), key="rightCol")],
]

# Create the window
window = sg.Window("Demo", layout)

# Create an event loop
while True:
    event, values = window.read()
    # End program if user closes window or
    # presses the OK button
    if event == sg.WIN_CLOSED:
        break
    # select transaction to ignore or include
    elif event == "transTable":
        print("TABLE EVENT", values[event])
        try:
            i = values[event][0]
            # toggle flag
            if instance.df.at[i, 'Ignore']:
                instance.df.at[i, 'Ignore'] = False
            else:
                instance.df.at[i, 'Ignore'] = True
            # update UI
            window["transTable"].update(values=instance.df.values.tolist(), row_colors=getColorsForIgnored(instance.df))
            window["TotalSpent"].update(value=f"TotalSpent: ${sumValidDebits(instance.df)}")
        except:
            print("exception")
            pass
    # select category to highlight
    elif event == "AllCategories":
        tab_ind = values[event][0]
        catSelected = instance.df_cat.at[tab_ind, "Category"]

        print(f'selected category index: {tab_ind}, {catSelected}')
        cols = getColorsForCategory(instance.df, catSelected)
        window["transTable"].update(values=instance.df.values.tolist(), row_colors=cols)

    # elif event == "FileList":
    #

    elif event == "OK":
        selectedFiles = window["FileList"].get()

        # load new data
        if len(selectedFiles) == 1:
            print("current files selected:", window["FileList"].get())
            instance = Main(selectedFiles[0])
            window["DateRange"].update(getCSVDateRange())
            window["TotalSpent"].update(f"TotalSpent: ${sumValidDebits(instance.df)}   ")

        # repopulate tables
        window["transTable"].update(values=instance.df.values.tolist(), row_colors=getColorsForIgnored(instance.df))
        window["AllCategories"].update(values=instance.df_cat.values.tolist())

window.close()

# END
