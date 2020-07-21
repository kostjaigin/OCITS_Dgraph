import easygui

def main():
    easygui.msgbox("Please, select the data folder ('facebook') using the file dialog")
    path = easygui.diropenbox()
    print(path)

if __name__ == '__main__':
    main()