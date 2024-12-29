# import dependencies
import sys
from os import path, kill, remove, listdir
from win32api import EnumDisplayMonitors, GetMonitorInfo
from win32gui import IsWindowVisible, ShowWindow, EnumWindows, GetWindowRect, MoveWindow
from win32con import SW_HIDE
from win32process import GetWindowThreadProcessId
from ctypes import windll, c_void_p
from math import ceil
from time import sleep
from psutil import Process
from subprocess import Popen
from threading import Thread
import customtkinter
from CTkMessagebox import CTkMessagebox
from pynput.mouse import Controller
from json import dump, load
import re

def is_admin():
    return windll.shell32.IsUserAnAdmin() == 1

if not is_admin():
    windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None)
    exit()

for listdiritem in listdir("."):
    if re.match(r'emt',listdiritem,flags=re.IGNORECASE):
        emtgenpath = listdiritem

# close splash screen and set directory
if getattr(sys, "frozen", False):
    import pyi_splash
    pyi_splash.close()
    directory = path.dirname(sys.executable)
    sys.path.append(directory)
else:
    directory = path.dirname(path.abspath(__file__))

# setup paths
save_path = path.join(directory, "advanced_settings.json")
exe_path = path.join(directory, emtgenpath, "client.exe")
update_path = path.join(directory, emtgenpath, "Emtgen2_Patcher.exe")
config_path = path.join(directory, emtgenpath, "config.cfg")

# set to previously set scale if exists
if path.exists(save_path):
    with open(save_path, 'r') as json_file:
        loaded_data = load(json_file)
        settings = loaded_data["settings"]
        scale = round((int(settings["scale"].replace("%", "")) / 100), 1)
        customtkinter.set_widget_scaling(scale)
        customtkinter.set_window_scaling(scale)



if path.exists(config_path):
    cfg_file = open(config_path, 'r')
    cfg_lines = cfg_file.readlines()
    clean_cfg_lines = []
    for cfg_line in cfg_lines:
        cfg_line_first = re.sub(r'\t{1,}',' ',cfg_line)
        cfg_line_second = re.sub(r'\n{1,}','',cfg_line_first)
        if not (cfg_line_second == ""):
            clean_cfg_lines.append(cfg_line_second) 

# set app theme
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme(".\\red.json")

# main GUI app
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Emtgen Advanced Launcher")
        if path.exists(update_path):
            self.wm_iconbitmap(update_path)

        # window size and position
        window_width = 720
        window_height = 500
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        scale_factor = self._get_window_scaling()
        x = int(((screen_width/2) - (window_width/2)) * scale_factor)
        y = int(((screen_height/2) - (window_height/2)) * scale_factor)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.lift()
        self.attributes('-topmost', 1)
        self.attributes('-topmost', 0)

        # configure grid layout (3 rows x 2 columns)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # setup text fonts
        self.title_font = customtkinter.CTkFont(size=20, weight="bold")
        self.subtitle_font = customtkinter.CTkFont(size=15, weight="bold", underline=True)
        self.label_font = customtkinter.CTkFont(size=15)

        # create sidebar frame
        self.sidebar_frame = customtkinter.CTkScrollableFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.columnconfigure(2, weight=1)
        self.windows_label = customtkinter.CTkLabel(self.sidebar_frame, text="Windows", font=self.title_font)
        self.windows_label.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=20, pady=(20, 10))
        self.sidebar_button_add = customtkinter.CTkButton(self.sidebar_frame, text="Add", command=self.sidebar_add_window)
        self.sidebar_button_add.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        # create start frame
        self.start_frame = customtkinter.CTkFrame(self, width=220, corner_radius=0)
        self.start_frame.grid(row=2, column=0, sticky="nsew")
        self.start_frame.columnconfigure(0, weight=1)
#        self.update_checkbox = customtkinter.CTkCheckBox(self.start_frame, text="Check for Update?", fg_color="green", hover_color="green")
#        self.update_checkbox.grid(row=0, column=0, sticky="w", padx=(10,0))
        self.start_button = customtkinter.CTkButton(self.start_frame, text="START", fg_color="green", hover_color="#006400", font=self.title_font, command=self.start)
        self.start_button.grid(row=1, column=0, sticky="nsew", padx=(10,25), pady=10)

        # create settings frame
        self.settings_frame = customtkinter.CTkFrame(self, fg_color=["gray92", "gray14"])
        self.settings_frame.grid(row=0, column=1, sticky="nsew")
        self.settings_frame.columnconfigure(3, weight=1)
        self.settings_label = customtkinter.CTkLabel(self.settings_frame, text="Settings", font=self.title_font)
        self.settings_label.grid(row=0, column=1, columnspan=5, sticky="nsew", padx=20,pady=(20,3))
        self.scale_label = customtkinter.CTkLabel(self.settings_frame, text="Scale:", font=self.label_font)
        self.scale_label.grid(row=0, column=1, sticky="w", padx=(10,0), pady=(20,3))
        self.scale_optionmenu = customtkinter.CTkOptionMenu(self.settings_frame, values=["40%", "60%", "80%", "100%", "120%", "140%", "160%"], width=100, command=self.set_scale)
        self.scale_optionmenu.grid(row=0, column=2, sticky="w", padx=(5,25), pady=(20,3))
        self.load_defaults_button = customtkinter.CTkButton(self.settings_frame, text="Paste", width=20, command=self.load_defaults)
        self.load_defaults_button.grid(row=0, column=4, padx=(0,10), sticky="e", pady=(20,3))
        self.save_defaults_button = customtkinter.CTkButton(self.settings_frame, text="Copy", width=20, command=self.save_defaults)
        self.save_defaults_button.grid(row=0, column=5, padx=(0,20), sticky="e", pady=(20,3))

        # create tabview
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=1, column=1, rowspan=2, padx=20, pady=(0,20), sticky="nsew")
        self.tabview.add("Video")
        self.tabview.add("Audio")
        self.tabview.add("Effects")
        self.tabview.add("Combat")
        self.tabview.add("Views")
        self.tabview.add("Size")

        self.tabview.tab("Video").grid_columnconfigure(1, weight=1)
        self.tabview.tab("Audio").grid_columnconfigure(2, weight=1)
        self.tabview.tab("Effects").grid_columnconfigure(2, weight=1)
        self.tabview.tab("Combat").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Views").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Size").grid_columnconfigure(0, weight=1)

        ### VIDEO TAB ###
        self.video_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Video", font=self.title_font)
        self.video_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

        # fullscreen
        self.fullscreen_var = customtkinter.IntVar()
        self.fullscreen_switch = customtkinter.CTkSwitch(self.tabview.tab("Video"), text="Fullscreen", variable=self.fullscreen_var, onvalue=1, offvalue=0, command=self.fullscreen_event)
        self.fullscreen_switch.grid(row=2, column=0, sticky="nw", padx=2, pady=2)
        self.fullscreen_optionmenu = customtkinter.CTkOptionMenu(self.tabview.tab("Video"), values=self.get_fulscreen_values())
        self.fullscreen_optionmenu.grid(row=2, column=1, sticky="nw", padx=2, pady=2)

        # monitor selection
        self.monitor_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Monitor", font=self.label_font)
        self.monitor_label.grid(row=3, column=0, sticky="nw", padx=2, pady=2)
        self.display_optionmenu = customtkinter.CTkOptionMenu(self.tabview.tab("Video"), values=self.get_monitor_values())
        self.display_optionmenu.grid(row=3, column=1, sticky="nw", padx=2, pady=2)
        
        # validation for size fields
        size_validation = (self.register(self.size_val), "%P")

        # width_start
        self.width_start_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Width Start (0-100%)", font=self.label_font)
        self.width_start_label.grid(row=4, column=0, sticky="nw", padx=2, pady=2)
        self.width_start_entry = customtkinter.CTkEntry(self.tabview.tab("Video"), validate="key", validatecommand=size_validation)
        self.width_start_entry.grid(row=4, column=1, sticky="nw", padx=2, pady=2)

        # width_end
        self.width_end_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Width End (0-100%)", font=self.label_font)
        self.width_end_label.grid(row=5, column=0, sticky="nw", padx=2, pady=2)
        self.width_end_entry = customtkinter.CTkEntry(self.tabview.tab("Video"), validate="key", validatecommand=size_validation)
        self.width_end_entry.grid(row=5, column=1, sticky="nw", padx=2, pady=2)

        # height_start
        self.height_start_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Height Start (0-100%)", font=self.label_font)
        self.height_start_label.grid(row=6, column=0, sticky="nw", padx=2, pady=2)
        self.height_start_entry = customtkinter.CTkEntry(self.tabview.tab("Video"), validate="key", validatecommand=size_validation)
        self.height_start_entry.grid(row=6, column=1, sticky="nw", padx=2, pady=2)

        # height_end
        self.height_end_label = customtkinter.CTkLabel(self.tabview.tab("Video"), text="Height End (0-100%)", font=self.label_font)
        self.height_end_label.grid(row=7, column=0, sticky="nw", padx=2, pady=2)
        self.height_end_entry = customtkinter.CTkEntry(self.tabview.tab("Video"), validate="key", validatecommand=size_validation)
        self.height_end_entry.grid(row=7, column=1, sticky="nw", padx=2, pady=2)

        ### AUDIO TAB ###
        self.audio_label = customtkinter.CTkLabel(self.tabview.tab("Audio"), text="Audio", font=self.title_font)
        self.audio_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

        # sfx
        self.sfx_label = customtkinter.CTkLabel(self.tabview.tab("Audio"), text="Sound Effects", font=self.label_font)
        self.sfx_label.grid(row=1, column=0, sticky="nw", padx=2, pady=2)
        self.sfx_number = customtkinter.IntVar(value=0)
        self.sfx_slider = customtkinter.CTkSlider(self.tabview.tab("Audio"), from_=0, to=5, number_of_steps=5, command=self.set_sfx)
        self.sfx_slider.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        self.sfx_number_label = customtkinter.CTkLabel(self.tabview.tab("Audio"), textvariable=self.sfx_number, font=self.label_font)
        self.sfx_number_label.grid(row=1, column=2, sticky="nw", padx=2, pady=2)

        # bgm
        self.bgm_label = customtkinter.CTkLabel(self.tabview.tab("Audio"), text="Background Music", font=self.label_font)
        self.bgm_label.grid(row=2, column=0, sticky="nw", padx=2, pady=2)
        self.bgm_number = customtkinter.DoubleVar()
        self.bgm_number_str = customtkinter.StringVar()
        self.bgm_number.trace_add("write", self.update_bgm_number_str)
        self.bgm_slider = customtkinter.CTkSlider(self.tabview.tab("Audio"), from_=0, to=1, number_of_steps=20, command=self.set_bgm)
        self.bgm_slider.grid(row=2, column=1, sticky="ew", padx=2, pady=2)
        self.bgm_number_label = customtkinter.CTkLabel(self.tabview.tab("Audio"), textvariable=self.bgm_number_str, font=self.label_font)
        self.bgm_number_label.grid(row=2, column=2, sticky="nw", padx=2, pady=2)

        ### EFFECTS TAB ###
        self.effects_label = customtkinter.CTkLabel(self.tabview.tab("Effects"), text="Effects", font=self.title_font)
        self.effects_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

        # names
        self.names_switch = customtkinter.CTkSwitch(self.tabview.tab("Effects"), text="Show Names")
        self.names_switch.grid(row=2, column=0, sticky="nw", padx=2, pady=2)

        # item preview
        self.model_switch = customtkinter.CTkSwitch(self.tabview.tab("Effects"), text="Show Model Preview")
        self.model_switch.grid(row=5, column=0, sticky="nw", padx=2, pady=2)

        # metin2 cursor
        self.cursor_switch = customtkinter.CTkSwitch(self.tabview.tab("Effects"), text="Use Emtgen Cursor")
        self.cursor_switch.grid(row=6, column=0, sticky="nw", padx=2, pady=2)

        # fov
        self.fov_label = customtkinter.CTkLabel(self.tabview.tab("Effects"), text="FOV", font=self.label_font)
        self.fov_label.grid(row=7, column=0, sticky="nw", padx=2, pady=2)
        self.fov_number = customtkinter.IntVar(value=0)
        self.fov_slider = customtkinter.CTkSlider(self.tabview.tab("Effects"), from_=0, to=90, number_of_steps=90, command=self.set_fov)
        self.fov_slider.grid(row=7, column=1, sticky="ew", padx=2, pady=2)
        self.fov_number_label = customtkinter.CTkLabel(self.tabview.tab("Effects"), textvariable=self.fov_number, font=self.label_font)
        self.fov_number_label.grid(row=7, column=2, sticky="nw", padx=2, pady=2)

        # shadows
        self.shadow_label = customtkinter.CTkLabel(self.tabview.tab("Effects"), text="Shadows", font=self.label_font)
        self.shadow_label.grid(row=9, column=0, sticky="nw", padx=2, pady=2)
        self.shadow_options = ["None", "Background", "Background + Player", "All"]
        self.shadow_optionmenu = customtkinter.CTkOptionMenu(self.tabview.tab("Effects"), width=175, values=self.shadow_options)
        self.shadow_optionmenu.grid(row=9, column=1, sticky="nw", padx=2, pady=2)

        # shadows qual
        self.shadowqual_label = customtkinter.CTkLabel(self.tabview.tab("Effects"), text="Shadows Quality", font=self.label_font)
        self.shadowqual_label.grid(row=10, column=0, sticky="nw", padx=2, pady=2)
        self.shadowqual_options = ["Low", "Mid", "High", "Extra"]
        self.shadowqual_optionmenu = customtkinter.CTkOptionMenu(self.tabview.tab("Effects"), width=175, values=self.shadowqual_options)
        self.shadowqual_optionmenu.grid(row=10, column=1, sticky="nw", padx=2, pady=2)

        # postprocessing
        self.postprocessing_switch = customtkinter.CTkSwitch(self.tabview.tab("Effects"), text="Post-Processing")
        self.postprocessing_switch.grid(row=11, column=0, sticky="nw", padx=2, pady=2)

        ### COMBAT TAB ###
        self.combat_label = customtkinter.CTkLabel(self.tabview.tab("Combat"), text="Combat", font=self.title_font)
        self.combat_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)


        self.monsters_label = customtkinter.CTkLabel(self.tabview.tab("Combat"), text="Monsters", font=self.subtitle_font)
        self.monsters_label.grid(row=2, column=0, sticky="nw", padx=2, pady=2)

        # dogmode
        self.dogmode_switch = customtkinter.CTkSwitch(self.tabview.tab("Combat"), text="Use Dog-mode")
        self.dogmode_switch.grid(row=3, column=0, sticky="nw", padx=2, pady=2)

        # damage
        self.damage_switch = customtkinter.CTkSwitch(self.tabview.tab("Combat"), text="Show Damage to Others")
        self.damage_switch.grid(row=7, column=0, sticky="nw", padx=2, pady=2,)

        ### FUNCTIONAL TAB ###
        self.functional_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Views", font=self.title_font)
        self.functional_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

        self.dohled_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Dohled na", font=self.subtitle_font)
        self.dohled_label.grid(row=1, column=0, sticky="nw", padx=2, pady=2)

        # View to WB, view_wb
        self.view_wb_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Worldboss", font=self.label_font)
        self.view_wb_label.grid(row=2, column=0, sticky="nw", padx=2, pady=2)
        self.view_wb_number = customtkinter.IntVar(value=0)
        self.view_wb_slider = customtkinter.CTkSlider(self.tabview.tab("Views"), from_=0.00, to=1.00, number_of_steps=100, command=self.set_view_wb)
        self.view_wb_slider.grid(row=2, column=1, sticky="ew", padx=2, pady=2)
        self.view_wb_number_label = customtkinter.CTkLabel(self.tabview.tab("Views"), textvariable=self.view_wb_number, font=self.label_font)
        self.view_wb_number_label.grid(row=2, column=2, sticky="nw", padx=2, pady=2)

        # View to pet, view_pet
        self.view_pet_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Pet", font=self.label_font)
        self.view_pet_label.grid(row=3, column=0, sticky="nw", padx=2, pady=2)
        self.view_pet_number = customtkinter.IntVar(value=0)
        self.view_pet_slider = customtkinter.CTkSlider(self.tabview.tab("Views"), from_=0.00, to=1.00, number_of_steps=100, command=self.set_view_pet)
        self.view_pet_slider.grid(row=3, column=1, sticky="ew", padx=2, pady=2)
        self.view_pet_number_label = customtkinter.CTkLabel(self.tabview.tab("Views"), textvariable=self.view_pet_number, font=self.label_font)
        self.view_pet_number_label.grid(row=3, column=2, sticky="nw", padx=2, pady=2)

        # View to mount, view_mount
        self.view_mount_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Mount", font=self.label_font)
        self.view_mount_label.grid(row=4, column=0, sticky="nw", padx=2, pady=2)
        self.view_mount_number = customtkinter.IntVar(value=0)
        self.view_mount_slider = customtkinter.CTkSlider(self.tabview.tab("Views"), from_=0.00, to=1.00, number_of_steps=100, command=self.set_view_mount)
        self.view_mount_slider.grid(row=4, column=1, sticky="ew", padx=2, pady=2)
        self.view_mount_number_label = customtkinter.CTkLabel(self.tabview.tab("Views"), textvariable=self.view_mount_number, font=self.label_font)
        self.view_mount_number_label.grid(row=4, column=2, sticky="nw", padx=2, pady=2)

        # View to mob, view_mob
        self.view_mob_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Mob", font=self.label_font)
        self.view_mob_label.grid(row=5, column=0, sticky="nw", padx=2, pady=2)
        self.view_mob_number = customtkinter.IntVar(value=0)
        self.view_mob_slider = customtkinter.CTkSlider(self.tabview.tab("Views"), from_=0.00, to=1.00, number_of_steps=100, command=self.set_view_mob)
        self.view_mob_slider.grid(row=5, column=1, sticky="ew", padx=2, pady=2)
        self.view_mob_number_label = customtkinter.CTkLabel(self.tabview.tab("Views"), textvariable=self.view_mob_number, font=self.label_font)
        self.view_mob_number_label.grid(row=5, column=2, sticky="nw", padx=2, pady=2)

        # View to buff, view_buff
        self.view_buff_label = customtkinter.CTkLabel(self.tabview.tab("Views"), text="Buff", font=self.label_font)
        self.view_buff_label.grid(row=6, column=0, sticky="nw", padx=2, pady=2)
        self.view_buff_number = customtkinter.IntVar(value=0)
        self.view_buff_slider = customtkinter.CTkSlider(self.tabview.tab("Views"), from_=0.00, to=1.00, number_of_steps=100, command=self.set_view_buff)
        self.view_buff_slider.grid(row=6, column=1, sticky="ew", padx=2, pady=2)
        self.view_buff_number_label = customtkinter.CTkLabel(self.tabview.tab("Views"), textvariable=self.view_buff_number, font=self.label_font)
        self.view_buff_number_label.grid(row=6, column=2, sticky="nw", padx=2, pady=2)

        # velikost

        self.size_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Size", font=self.title_font)
        self.size_label.grid(row=0, column=0, sticky="nw", padx=2, pady=2)

        self.velikost_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Velikost", font=self.subtitle_font)
        self.velikost_label.grid(row=1, column=0, sticky="nw", padx=2, pady=2)

        # Size of damage, size_damage
        self.size_damage_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Damage", font=self.label_font)
        self.size_damage_label.grid(row=2, column=0, sticky="nw", padx=2, pady=2)
        self.size_damage_number = customtkinter.IntVar(value=0)
        self.size_damage_slider = customtkinter.CTkSlider(self.tabview.tab("Size"), from_=0.15, to=2.50, number_of_steps=235, command=self.set_size_damage)
        self.size_damage_slider.grid(row=2, column=1, sticky="ew", padx=2, pady=2)
        self.size_damage_number_label = customtkinter.CTkLabel(self.tabview.tab("Size"), textvariable=self.size_damage_number, font=self.label_font)
        self.size_damage_number_label.grid(row=2, column=2, sticky="nw", padx=2, pady=2)

        # Size of boss, size_boss
        self.size_boss_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Boss", font=self.label_font)
        self.size_boss_label.grid(row=3, column=0, sticky="nw", padx=2, pady=2)
        self.size_boss_number = customtkinter.IntVar(value=0)
        self.size_boss_slider = customtkinter.CTkSlider(self.tabview.tab("Size"), from_=100, to=150, number_of_steps=50, command=self.set_size_boss)
        self.size_boss_slider.grid(row=3, column=1, sticky="ew", padx=2, pady=2)
        self.size_boss_number_label = customtkinter.CTkLabel(self.tabview.tab("Size"), textvariable=self.size_boss_number, font=self.label_font)
        self.size_boss_number_label.grid(row=3, column=2, sticky="nw", padx=2, pady=2)

        # Size of stone, size_stone
        self.size_stone_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Kameny", font=self.label_font)
        self.size_stone_label.grid(row=4, column=0, sticky="nw", padx=2, pady=2)
        self.size_stone_number = customtkinter.IntVar(value=0)
        self.size_stone_slider = customtkinter.CTkSlider(self.tabview.tab("Size"), from_=100, to=200, number_of_steps=100, command=self.set_size_stone)
        self.size_stone_slider.grid(row=4, column=1, sticky="ew", padx=2, pady=2)
        self.size_stone_number_label = customtkinter.CTkLabel(self.tabview.tab("Size"), textvariable=self.size_stone_number, font=self.label_font)
        self.size_stone_number_label.grid(row=4, column=2, sticky="nw", padx=2, pady=2)

        # Size of mount, size_mount
        self.size_mount_label = customtkinter.CTkLabel(self.tabview.tab("Size"), text="Mount", font=self.label_font)
        self.size_mount_label.grid(row=5, column=0, sticky="nw", padx=2, pady=2)
        self.size_mount_number = customtkinter.IntVar(value=0)
        self.size_mount_slider = customtkinter.CTkSlider(self.tabview.tab("Size"), from_=50, to=100, number_of_steps=50, command=self.set_size_mount)
        self.size_mount_slider.grid(row=5, column=1, sticky="ew", padx=2, pady=2)
        self.size_mount_number_label = customtkinter.CTkLabel(self.tabview.tab("Size"), textvariable=self.size_mount_number, font=self.label_font)
        self.size_mount_number_label.grid(row=5, column=2, sticky="nw", padx=2, pady=2)

        # prepare loading screen
        self.loading = customtkinter.CTkLabel(self, text="Starting... Please Wait", font=customtkinter.CTkFont(size=50))

        # initialize values
        self.current_window = 1
        self.row_counter = 0

        self.delete_buttons = []
        self.edit_buttons = []
        self.buttons = []
        self.settings = []
        self.checkboxes = []

        # set default values
        self.defaults = {# Video
                         "xstart": 0, 
                         "xend": 100, 
                         "ystart": 0, 
                         "yend": 100, 
                         "fullscreen": 0, 
                         # Audio
                         "sfx": 0, 
                         "bgm": 0, 
                         # Effects
                         "names": 1, 
                         "model": 1, 
                         "cursor": 1, 
                         "fov": 25, 
                         "shadow": 0, 
                         "shadowqual": 0,
                         "postprocessing": 0,
                         # Combat
                         "dogmode": 0, 
                         "damage": 1, #enemy_dmg
                         # Views
                         "ime": 1,
                         "view_wb": 1,
                         "view_pet": 1,
                         "view_mount": 1,
                         "view_mob": 1,
                         "view_buff": 1,
                         "size_damage": 1,
                         "size_boss": 100.0,
                         "size_stone": 100.0,
                         "size_mount": 100.0,
                         # idk, the rest
                         "display": "Main", 
                         "fullscreenres": "800x600", 
                         "state": 0, "name": "New Window"}

        # configure custom events
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<<BackgroundTaskFinished>>", lambda event: self.show_all())

        # load values from file
        self.load_file()

    # get values for optionmenus
    def get_monitor_values(self):
        device = []
        for monitor in EnumDisplayMonitors():
            m_info = GetMonitorInfo(monitor[0])
            if m_info.get('Flags') == 1:
                device.append("Main")
            else:
                device.append(m_info.get('Device').split("\\")[-1])
        return device
    def get_fulscreen_values(self):
        all_res = ["800x600", "1024x768", "1152x864", "1280x720", "1280x768", "1280x800", "1280x960", "1280x1024", "1366x768", "1600x900", "1600x1024", "1600x1200", "1680x1050", "1920x1080", "1920x1200", "1920x1440", "2560x1440", "3840x2160"]
        possible_res = []
        for res in all_res:
            if int(res.split("x")[0]) <= self.winfo_screenwidth():
                possible_res.append(res)
        return possible_res

    # set values for optionmenus
    def set_scale(self, val):
        new_scaling_float = round((int(val.replace("%", "")) / 100),1)
        customtkinter.set_window_scaling(new_scaling_float)
        customtkinter.set_widget_scaling(new_scaling_float)

    # get / set defaults
    def save_defaults(self):
        self.defaults = self.get_values()
    def load_defaults(self):
        self.set_values(self.defaults)
        self.fullscreen_var.set(self.defaults["fullscreen"])
        self.fullscreen_event()

    # get / set values
    def set_values(self, values):
        self.width_start_entry.delete(0, customtkinter.END)
        self.width_start_entry.insert(0, str(values["xstart"]))
        self.width_end_entry.delete(0, customtkinter.END)
        self.width_end_entry.insert(0, str(values["xend"]))
        self.height_start_entry.delete(0, customtkinter.END)
        self.height_start_entry.insert(0, str(values["ystart"]))
        self.height_end_entry.delete(0, customtkinter.END)
        self.height_end_entry.insert(0, str(values["yend"]))
        self.fullscreen_switch.select() if values["fullscreen"] == 1 else self.fullscreen_switch.deselect()
        self.sfx_slider.set(values["sfx"])
        self.sfx_number.set(values["sfx"])
        self.bgm_slider.set(values["bgm"])
        self.bgm_number.set(values["bgm"])
        self.names_switch.select() if values["names"] == 1 else self.names_switch.deselect()
        self.model_switch.select() if values["model"] == 1 else self.model_switch.deselect()  
        self.cursor_switch.select() if values["cursor"] == 1 else self.cursor_switch.deselect() 
        self.fov_slider.set(values["fov"])
        self.fov_number.set(values["fov"])
        self.shadow_optionmenu.set(self.shadow_options[values["shadow"]])
        self.shadowqual_optionmenu.set(self.shadowqual_options[values["shadowqual"]])
        self.postprocessing_switch.select() if values["postprocessing"] == 1 else self.postprocessing_switch.deselect()
#        self.ime_switch.select() if values["ime"] == 1 else self.ime_switch.deselect()
        self.view_wb_slider.set(values["view_wb"])
        self.view_wb_number.set(values["view_wb"])
        self.view_pet_slider.set(values["view_pet"])
        self.view_pet_number.set(values["view_pet"])
        self.view_mount_slider.set(values["view_mount"])
        self.view_mount_number.set(values["view_mount"])
        self.view_mob_slider.set(values["view_mob"])
        self.view_mob_number.set(values["view_mob"])
        self.view_buff_slider.set(values["view_buff"])
        self.view_buff_number.set(values["view_buff"])
        self.size_damage_slider.set(values["size_damage"])
        self.size_damage_number.set(values["size_damage"])
        self.size_boss_slider.set(values["size_boss"])
        self.size_boss_number.set(values["size_boss"])
        self.size_stone_slider.set(values["size_stone"])
        self.size_stone_number.set(values["size_stone"])
        self.size_mount_slider.set(values["size_mount"])
        self.size_mount_number.set(values["size_mount"])
        
        self.display_optionmenu.set(values["display"])
        self.fullscreen_optionmenu.set(values["fullscreenres"])
    def get_values(self):
        values = {"xstart": int(self.width_start_entry.get()),
                  "xend": int(self.width_end_entry.get()),
                  "ystart": int(self.height_start_entry.get()),
                  "yend": int(self.height_end_entry.get()),
                  "fullscreen": self.fullscreen_switch.get(),
                  "sfx": self.sfx_number.get(),
                  "bgm": self.bgm_number.get(),
                  "names": self.names_switch.get(),
                  "model": self.model_switch.get(),
                  "cursor": self.cursor_switch.get(),
                  "fov": self.fov_number.get(),
                  "shadow": self.shadow_options.index(self.shadow_optionmenu.get()),
                  "shadowqual": self.shadowqual_options.index(self.shadowqual_optionmenu.get()),
                  "postprocessing": self.postprocessing_switch.get(),
                  "dogmode": self.dogmode_switch.get(),
                  "damage": self.damage_switch.get(),
#                  "ime": self.ime_switch.get(),
                  "view_wb": self.view_wb_number.get(),
                  "view_pet": self.view_pet_number.get(),
                  "view_mount": self.view_mount_number.get(),
                  "view_mob": self.view_mob_number.get(),
                  "view_buff": self.view_buff_number.get(),
                  "size_damage": self.size_damage_number.get(),
                  "size_boss": self.size_boss_number.get(),
                  "size_stone": self.size_stone_number.get(),
                  "size_mount": self.size_mount_number.get(),
                  "display": self.display_optionmenu.get(),
                  "fullscreenres": self.fullscreen_optionmenu.get()}
        return values

    # side panel events
    def sidebar_delete_window(self, id):
        # delete the delete button
        for delete_button in self.delete_buttons:
            if delete_button[0] == id:
                delete_button[1].grid_forget()
                delete_button[1].destroy()
                self.delete_buttons.remove(delete_button)
                break

        # delete the edit button
        for edit_button in self.edit_buttons:
            if edit_button[0] == id:
                edit_button[1].grid_forget()
                edit_button[1].destroy()
                self.edit_buttons.remove(edit_button)
                break

        # delete the window button
        for button in self.buttons:
            if button[0] == id:
                button[1].grid_forget()
                button[1].destroy()
                self.buttons.remove(button)
                break

        # delete the checkbox
        for checkbox in self.checkboxes:
            if checkbox[0] == id:
                checkbox[1].grid_forget()
                checkbox[1].destroy()
                self.checkboxes.remove(checkbox)
                break
        
        # delete the settings
        for setting in self.settings:
            if setting[0] == id:
                self.settings.remove(setting)
                break
        
        # hide settings if no button
        if len(self.buttons) == 0:
            self.settings_event()
        
        # if active button was delete
        elif id == self.current_window:

            # select the last button
            self.buttons[-1][1].configure(fg_color=["#325882", "#14375e"])
            self.current_window = self.buttons[-1][0]

            # get settings for last button
            for list in self.settings:
                if list[0] == self.current_window:
                    self.set_values(list[1])
                    break    
    def rename_window(self, id):
        for button, window in zip(self.buttons,self.settings):
            if button[0] == id:
                previous_name = button[1].cget("text")
                dialog = customtkinter.CTkInputDialog(text="Type in a new name:", title=f"Rename {previous_name}",)
                mouse = Controller()
                position = mouse.position
                dialog.geometry("+"+str(position[0])+"+"+str(position[1]))
                out = dialog.get_input()
                if out != None:
                    button[1].configure(text=out)
                    window[1]["name"] = out
                break
    def sidebar_button_event(self, b_id):
        # save values of previous window
        for list in self.settings:
            if list[0] == self.current_window:
                list[1].update(self.get_values())
                break

        # set the pressed window to current
        for button in self.buttons:
            if button[0] == b_id:
                button[1].configure(fg_color=["#800000", "#800000"])
                self.current_window = button[0]
            else:
                button[1].configure(fg_color=["#C08261", "#C08261"])
                
        # show values for current window
        for list in self.settings:
            if list[0] == self.current_window:
                self.set_values(list[1])
                self.fullscreen_var.set(list[1]["fullscreen"])
                self.fullscreen_event()
                break
    def checkbox_event(self, id):
        for checkbox, setting in zip(self.checkboxes,self.settings):
            if setting[0] == id:
                setting[1]["state"] = checkbox[1].get()
                break
    def sidebar_add_window(self, settings={}):
        self.row_counter += 1
        button_id = self.row_counter

        # add delete button
        delete_button = customtkinter.CTkButton(self.sidebar_frame, text="X", fg_color="red", width=28, hover_color="#8B0000", font=customtkinter.CTkFont(size=15, weight="bold"), command=lambda b_id=button_id: self.sidebar_delete_window(b_id))
        delete_button.grid(row=self.row_counter, column=0, padx=5, pady=5, sticky="nws")

        # add edit button
        edit_name_button = customtkinter.CTkButton(self.sidebar_frame, text="E", fg_color="#ff7900", width=28, hover_color="#b35500", font=customtkinter.CTkFont(size=15, weight="bold"), command=lambda b_id=button_id: self.rename_window(b_id))
        edit_name_button.grid(row=self.row_counter, column=1, padx=(0,5), pady=5, sticky="nws")

        # add window button
        sidebar_button = customtkinter.CTkButton(self.sidebar_frame, text="New Window", command=lambda b_id=button_id: self.sidebar_button_event(b_id))
        sidebar_button.grid(row=self.row_counter, column=2, padx=(0,5), pady=5,sticky="nsew")

        # add checkbox
        checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="", hover_color="green",fg_color="green", width=24, command=lambda b_id=button_id: self.checkbox_event(b_id))
        checkbox.grid(row=self.row_counter, column=3, pady=5, sticky="nws")

        # move add button down
        self.sidebar_button_add.grid(row=self.row_counter+1, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        # save widgets
        if settings == {}:
            self.settings.append([button_id,self.defaults.copy()])
            self.buttons.append([button_id,sidebar_button])
            self.checkboxes.append([button_id,checkbox])
        else:
            sidebar_button.configure(text=settings["name"])
            checkbox.select() if settings["state"] == 1 else checkbox.deselect()

            self.settings.append([button_id,settings.copy()])
            self.buttons.append([button_id,sidebar_button])
            self.checkboxes.append([button_id,checkbox])

        self.edit_buttons.append([button_id,edit_name_button])
        self.delete_buttons.append([button_id,delete_button])
        self.sidebar_button_event(button_id)
        
        # show settings if windows exists
        self.settings_event()

    # hide / show UI
    def fullscreen_event(self):
        val = self.fullscreen_var.get()
        if val == 1:
            self.display_optionmenu.grid_forget()
            self.monitor_label.grid_forget()
            self.width_start_entry.grid_forget()
            self.width_start_label.grid_forget()
            self.width_end_entry.grid_forget()
            self.width_end_label.grid_forget()
            self.height_start_entry.grid_forget()
            self.height_start_label.grid_forget()
            self.height_end_entry.grid_forget()
            self.height_end_label.grid_forget()
            self.fullscreen_optionmenu.grid(row=2, column=1, sticky="nw", padx=2, pady=2)
        elif val == 0:
            self.display_optionmenu.grid(row=3, column=1, sticky="nw", padx=2, pady=2)
            self.monitor_label.grid(row=3, column=0, sticky="nw", padx=2, pady=2)
            self.width_start_entry.grid(row=4, column=1, sticky="nw", padx=2, pady=2)
            self.width_start_label.grid(row=4, column=0, sticky="nw", padx=2, pady=2)
            self.width_end_entry.grid(row=5, column=1, sticky="nw", padx=2, pady=2)
            self.width_end_label.grid(row=5, column=0, sticky="nw", padx=2, pady=2)
            self.height_start_entry.grid(row=6, column=1, sticky="nw", padx=2, pady=2)
            self.height_start_label.grid(row=6, column=0, sticky="nw", padx=2, pady=2)
            self.height_end_entry.grid(row=7, column=1, sticky="nw", padx=2, pady=2)
            self.height_end_label.grid(row=7, column=0, sticky="nw", padx=2, pady=2)
            self.fullscreen_optionmenu.grid_forget()
    def settings_event(self):
        if len(self.buttons) == 0:
            self.tabview.grid_forget()
            self.save_defaults_button.grid_forget()
            self.load_defaults_button.grid_forget()   
        elif len(self.buttons) >= 0:
            self.tabview.grid(row=1, column=1, rowspan=2, padx=20, pady=15, sticky="nsew")
            self.load_defaults_button.grid(row=0, column=4, padx=(0,10), pady=(20,3), sticky="e")
            self.save_defaults_button.grid(row=0, column=5, padx=(0,20), pady=(20,3), sticky="e")
    def hide_all(self):
        self.start_frame.grid_forget()
        self.sidebar_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.tabview.grid_forget()

        self.loading.grid(row=0, column=0, rowspan=50, columnspan=50, sticky="nsew", padx=20, pady=20)
    def show_all(self):
        self.loading.grid_forget()

        self.start_frame.grid(row=2, column=0, sticky="nsew")
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.settings_frame.grid(row=0, column=1, sticky="nsew")
        self.tabview.grid(row=1, column=1, rowspan=2, padx=20, pady=(0,20), sticky="nsew")
        self.start_button.configure(state="normal")

    # update labels with sliders
    def set_sfx(self, val):
        self.sfx_number.set(round(val))
    def set_bgm(self, val):
        self.bgm_number.set(round(val,3))
    def set_fov(self, val):
        self.fov_number.set(round(val))
    def update_bgm_number_str(self, *args):
        self.bgm_number_str.set(f"{self.bgm_number.get():.3f}")

    def set_view_wb(self, val):
        self.view_wb_number.set(round(val,3))
    def set_view_pet(self, val):
        self.view_pet_number.set(round(val,3))
    def set_view_mount(self, val):
        self.view_mount_number.set(round(val,3))
    def set_view_mob(self, val):
        self.view_mob_number.set(round(val,3))
    def set_view_buff(self, val):
        self.view_buff_number.set(round(val,3))
    def set_size_damage(self, val):
        self.size_damage_number.set(round(val,3))
    def set_size_boss(self, val):
        self.size_boss_number.set(round(val,3))
    def set_size_stone(self, val):
        self.size_stone_number.set(round(val,3))
    def set_size_mount(self, val):
        self.size_mount_number.set(round(val,3))
    

    # validation for entry fields
    def size_val(self, P):
        if P == "":
            return True
        if P.isdigit():
            if (0 <= int(P) <= 100):
                if int(P[0]) == 0 and len(P) > 1:
                    return False
                return True
            return False
        return False

    # start button event
    def start(self):
        self.start_button.configure(state="disabled")
        self.save_file()

        # check if at least one window exists
        if len(self.settings) == 0:
            CTkMessagebox(master=self, title="Warning Message!", message=f"Please create and select at least one window", icon="warning")
            self.start_button.configure(state="normal")
            return
        
        # check if at least one window is selected
        count = 0
        for d in self.settings:
            if d[1]["state"] == 1:
                count += 1
                break

        if count == 0:
            CTkMessagebox(master=self, title="Warning Message!", message=f"Please select at least one window to start", icon="warning")
            self.start_button.configure(state="normal")
            return
        
        # check if patcher exists
#        if self.update_checkbox.get() == 1:
#            if not path.exists(update_path):
#                CTkMessagebox(master=self, title="Warning Message!", message=f"Cannot find Emtgen2_Patcher.exe, please rename your launcher", icon="warning")
#                self.start_button.configure(state="normal")
#                return

        # check if fullscreen is on its own
        fs = any(d[1]['fullscreen'] == 1 and d[1]['state'] == 1 for d in self.settings)
        if fs:
            count = sum(d[1]['state'] == 1 for d in self.settings)
            if count > 1:
                CTkMessagebox(master=self, title="Warning Message!", message="Fullscreen windows can only be opened on its own, please deselect other windows", icon="warning")
                self.start_button.configure(state="normal")
                return  
            
        # check values
        for window, but in zip(self.settings,self.buttons):
            if window[1]["state"] == 1:
                if window[1]["fullscreen"] == 1:
                    possible_res = self.get_fulscreen_values()
                    if window[1]["fullscreenres"] not in possible_res:
                        CTkMessagebox(master=self, title="Warning Message!", message=f"Please select a valid resolution in {but[1].cget("text")}", icon="warning")
                        self.fullscreen_optionmenu.configure(values=possible_res.copy())
                        self.start_button.configure(state="normal")
                else:
                    if window[1]["xstart"] == "" or window[1]["xend"] == "" or window[1]["ystart"] == "" or window[1]["yend"] == "":
                        CTkMessagebox(master=self, title="Warning Message!", message=f"Please fill out all Video fields in {but[1].cget("text")}", icon="warning")
                        self.start_button.configure(state="normal")
                        return
                    if window[1]["xend"] <= window[1]["xstart"]:
                        CTkMessagebox(master=self, title="Warning Message!", message=f"Width start must be smaller than Width end in {but[1].cget("text")}", icon="warning")
                        self.start_button.configure(state="normal")
                        return
                    if window[1]["yend"] <= window[1]["ystart"]:
                        CTkMessagebox(master=self, title="Warning Message!", message=f"Height start must be smaller than Height end in {but[1].cget("text")}", icon="warning")
                        self.start_button.configure(state="normal")
                        return
                    device = self.get_monitor_values()
                    if window[1]["display"] not in device:
                        CTkMessagebox(master=self, title="Warning Message!", message=f"Please select a valid monitor in {but[1].cget("text")}", icon="warning")
                        self.display_optionmenu.configure(values=device.copy())
                        self.start_button.configure(state="normal")
                        return

        def open_emtgen():
            windll.user32.SetThreadDpiAwarenessContext(c_void_p(-1))

            minfo = []
            for monitor in EnumDisplayMonitors():
                minfo.append(GetMonitorInfo(monitor[0]))

            def combine_values(values):
                # get the working area
                work_area = []
                for item in minfo:
                    if item['Device'].split("\\")[-1] == values["display"] or (item['Flags'] == 1 and values["display"] == "Main"):
                        work_area = item['Work']
                        break

                # calculate width and height
                if values["fullscreen"] == 1:
                    res = values["fullscreenres"].split("x")
                    width = res[0]
                    height = res[1]
                elif values["fullscreen"] == 0:
                    width = ceil(((abs(int(values["xend"])-int(values["xstart"]))) / 100) * (work_area[2] - work_area[0]))
                    height = ceil((((abs(int(values["yend"])-int(values["ystart"]))) / 100) * (work_area[3] - work_area[1])) - windll.user32.GetSystemMetrics(4) - 8)

                settings = []
                for clean_cfg_line in clean_cfg_lines:
                    ###### Video tab
                    if re.match("WIDTH",clean_cfg_line):
                        clean_cfg_line = "WIDTH " + str(width)
                    if re.match("HEIGHT",clean_cfg_line):
                        clean_cfg_line = "HEIGHT " + str(height)
                    if re.match("WINDOWED",clean_cfg_line):
                        clean_cfg_line = "WINDOWED " + str(1 if values["fullscreen"] == 0 else 0)
                    ###### Audio tab
                    if re.match("VOICE_VOLUME",clean_cfg_line):
                        clean_cfg_line = "VOICE_VOLUME " + str(values["sfx"])
                    if re.match("MUSIC_VOLUME",clean_cfg_line):
                        clean_cfg_line = "MUSIC_VOLUME " + str(f"{values["bgm"]:.3f}")
                    ###### Effects tab
                    if re.match("ALWAYS_VIEW_NAME_ITEMS",clean_cfg_line):
                        clean_cfg_line = "ALWAYS_VIEW_NAME_ITEMS " + str(values["names"])
                    if re.match("RENDER_TARGET",clean_cfg_line):
                        clean_cfg_line = "RENDER_TARGET " + str(values["model"])
                    if re.match("SOFTWARE_CURSOR",clean_cfg_line):
                        clean_cfg_line = "SOFTWARE_CURSOR " + str(1 if values["cursor"] == 0 else 0)
                    if re.match("FOV", clean_cfg_line):
                        clean_cfg_line = "FOV " + str(values["fov"])
                    if re.match("SHADOW_TARGET_LEVEL_N", clean_cfg_line):
                        clean_cfg_line = "SHADOW_TARGET_LEVEL_N " + str(values["shadow"])
                    if re.match("SHADOW_QUALITY_LEVEL", clean_cfg_line):
                        clean_cfg_line = "SHADOW_QUALITY_LEVEL " + str(values["shadowqual"])
                    ###### Combat tab
                    if re.match("DOG_MODE_ON", clean_cfg_line):
                        clean_cfg_line = "DOG_MODE_ON " +str(values["dogmode"])
                    if re.match("ENEMY_DMG",clean_cfg_line):
                        clean_cfg_line = "ENEMY_DMG " + str(values["damage"])
                    ###### Views
                    if re.match("SHOP_RANGE", clean_cfg_line):
                        clean_cfg_line = "SHOP_RANGE " + str(values["view_wb"])
                    if re.match("PET_RANGE", clean_cfg_line):
                        clean_cfg_line = "PET_RANGE " + str(values["view_pet"])
                    if re.match("MOUNT_RANGE", clean_cfg_line):
                        clean_cfg_line = "MOUNT_RANGE " + str(values["view_mount"])
                    if re.match("MONSTER_RANGE", clean_cfg_line):
                        clean_cfg_line = "MONSTER_RANGE " + str(values["view_mob"])
                    if re.match("PLAYER_RANGE", clean_cfg_line):
                        clean_cfg_line = "PLAYER_RANGE " + str(values["view_buff"])
                    ###### Size
                    if re.match("DAMAGE_SCALE", clean_cfg_line):
                        clean_cfg_line = "DAMAGE_SCALE " + str(f"{values["size_damage"]:.4f}")
                    if re.match("BOSS_SCALE", clean_cfg_line):
                        clean_cfg_line = "BOSS_SCALE " + str(f"{values["size_boss"]:.3f}")
                    if re.match("MOUNT_SCALE", clean_cfg_line):
                        clean_cfg_line = "MOUNT_SCALE " + str(f"{values["size_mount"]:.3f}")
                    if re.match("STONE_SCALE", clean_cfg_line):
                        clean_cfg_line = "STONE_SCALE " + str(f"{values["size_stone"]:.3f}")
                        
                        
                        
                    settings.append(clean_cfg_line)
                return settings

            windows_to_start = []
            for window in self.settings:
                if window[1]["state"] == 1:
                        if window[1]["fullscreen"] == 0:
                            for item in minfo:
                                if item['Device'].split("\\")[-1] == window[1]["display"] or (item['Flags'] == 1 and window[1]["display"] == "Main"):
                                    work_area = item['Work']
                                    break
                            x = int((int(window[1]["xstart"]) / 100) * (work_area[2]-work_area[0])) -8 + work_area[0]
                            y = int((int(window[1]["ystart"]) / 100) * (work_area[3]-work_area[1])) + work_area[1]
                        elif window[1]["fullscreen"] == 1:
                            x = 0
                            y = 0
                        windows_to_start.append({"x":x,"y":y,"config":combine_values(window[1]),"fullscreen":window[1]["fullscreen"]})

#            if self.update_checkbox.get() == 1:
#                uphwnds = []
#                def updateEnumHandler(uphwnd, ctx):
#                    if IsWindowVisible(uphwnd):
#                        _, process_id = GetWindowThreadProcessId(uphwnd)
#                        if process_id == ctx:
#                            ShowWindow(uphwnd, SW_HIDE)
#                            uphwnds.append(uphwnd)
#
#                process = Popen([update_path],cwd=path.join(directory, emtgenpath))
#                pidd = process.pid
#                p = Process(pidd)
#                while True:
#                    EnumWindows(updateEnumHandler, pidd)
#                    if len(uphwnds) > 0:
#                        break
#
#                while True:
#                    io_counters = p.io_counters() 
#                    read = io_counters[2]
#                    write = io_counters[3]
#                    sleep(10)
#                    io_counters_new = p.io_counters() 
#                    read_new = io_counters_new[2]
#                    write_new = io_counters_new[3]
#                    if read == read_new and write == write_new:
#                        kill(pidd,15)
#                        break

            key_lines = []
            if path.exists(config_path): 
                with open(config_path, 'r') as file:
                    lines = file.readlines()
                    for line in lines:
                        if line.startswith('KEY'):
                            key_lines.append(line.strip())

            pids = []
            with open(config_path, 'w') as file:
                for value in windows_to_start[0]["config"]:
                    file.write((value) + "\n")
                for key in key_lines:
                    file.write((key) + "\n")
            access_time_timestamp = path.getatime(config_path)
            process = Popen([exe_path],cwd=path.join(directory, emtgenpath))
            if windows_to_start[0]["fullscreen"] == 0:
                pids.append(process.pid)

            if len(windows_to_start) > 1:
                for window in windows_to_start[1:]:
                    while True:
                        access_time_timestamp_new = path.getatime(config_path)
                        if access_time_timestamp_new > access_time_timestamp:
                            sleep(0.1)
                            with open(config_path, 'w') as file:
                                for value in window["config"]:
                                    file.write((value) + "\n")
                                for key in key_lines:
                                    file.write((key) + "\n")
                            access_time_timestamp = path.getatime(config_path)
                            process = Popen([exe_path],cwd=path.join(directory, emtgenpath))
                            if window["fullscreen"] == 0:
                                pids.append(process.pid)
                            break

            hwnds = []
            com = []
            for win, pid in zip(windows_to_start,pids):
                if win["fullscreen"] == 0:
                    com.append({"x":win["x"],"y":win["y"],"pid":pid})

            def winEnumHandler(hwnd, ctx):
                if IsWindowVisible(hwnd):
                    _, process_id = GetWindowThreadProcessId(hwnd)
                    if process_id == ctx["pid"]:
                        rect = GetWindowRect(hwnd)
                        w = rect[2] - rect[0]
                        h = rect[3] - rect[1]
                        MoveWindow(hwnd, ctx["x"], ctx["y"], w, h, True)
                        hwnds.append(hwnd)
                        com.remove(ctx)

            while True:
                for vals in com:
                    EnumWindows(winEnumHandler, vals)
                if len(pids) == len(hwnds):
                    break

            self.event_generate("<<BackgroundTaskFinished>>", when="tail")

        # start opening windows
        self.hide_all()
        open_met = Thread(target=open_emtgen)
        open_met.start()

    # save / load json settings
    def load_file(self):
        if path.exists(save_path):
            # load JSON data
            with open(save_path, 'r') as json_file:
                loaded_data = load(json_file)

            # split to sections
            dictionaries = loaded_data["windows"]
            settings = loaded_data["settings"]

            # set settings to loaded values
            self.scale_optionmenu.set(settings["scale"])
#            self.update_checkbox.select() if settings["update"] == 1 else self.update_checkbox.deselect()
            self.defaults = settings["defaults"]

            if dictionaries != []:

                # set windows to loaded values
                self.set_values(dictionaries[0])
                for window in dictionaries:
                    self.sidebar_add_window(window)
                self.settings_event()

            else:
                # load defaults
                self.set_values(self.defaults)
                self.settings_event() 
        else:
            # load defaults
            self.scale_optionmenu.set("100%")
            self.set_values(self.defaults)
            self.settings_event() 
    def save_file(self):
        # save current window
        for list in self.settings:
            if list[0] == self.current_window:
                list[1].update(self.get_values())
                break

        # extract dictionaries
        dictionaries = [dictionary for _, dictionary in self.settings]

        # construct settings section
        setting = {"scale": self.scale_optionmenu.get(), "defaults": self.defaults}#, "update": self.update_checkbox.get()}

        # combine
        to_save = {"windows": dictionaries, "settings": setting}

        # save to JSON file
        with open(save_path, 'w') as json_file:
            dump(to_save, json_file, indent=4)

    # save on close
    def close(self):
        self.save_file()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()


