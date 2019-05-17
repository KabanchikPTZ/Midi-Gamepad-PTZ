import sys  # нужен для передачи argv в QApplication
from PyQt5 import QtWidgets
import design
import pygame
from onvif import ONVIFCamera, ONVIFService, ONVIFError
from time import sleep
import datetime
from pandaMini import MidiManager
import zeep
import threading
X_AXIS = 0
Y_AXIS = 1
THR_AXIS = 2
Z_AXIS = 3
midi= MidiManager()


def zeep_pythonvalue(self, xmlvalue):  # нужно для корректной работы камеры
    return xmlvalue


class Application(QtWidgets.QMainWindow, design.Ui_MainWindow):

    connected = True
    focusMode = False

    def __init__(self):
        # для доступа к переменным, методам и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # для инициализации дизайна
        self.done = False
        self.connectBtn.clicked.connect(self.connect)
        self.disconnectBtn.clicked.connect(self.disconnect_camera)
        self.contrastWasPressed = 0
        self.brightnessWasPressed = 0
        self.sharpnessWasPressed = 0
        self.saturWasPressed = 0
        self.preset1 = 0
        self.preset2 = 0
        self.preset3 = 0
        self.preset4 = 0
        self.preset5 = 0
        self.preset6 = 0
        self.preset7 = 0
        self.preset8 = 0



    def preset1ch(self, args = None, kwargs = None):
        self.preset1 =1
    def preset2ch(self, args = None, kwargs = None):
        self.preset2 =1
    def preset3ch(self, args = None, kwargs = None):
        self.preset3 =1
    def preset4ch(self, args = None, kwargs = None):
        self.preset4 =1
    def preset5ch(self, args = None, kwargs = None):
        self.preset5 =1
    def preset6ch(self, args = None, kwargs = None):
        self.preset6 =1
    def preset7ch(self, args = None, kwargs = None):
        self.preset7 =1
    def preset8ch(self, args = None, kwargs = None):
        self.preset8 =1

    def sharpnessPlus(self, args = None, kwargs = None):
        self.sharpnessWasPressed = 1
    def sharpnessMinus(self, args = None, kwargs = None):
        self.sharpnessWasPressed = -1
    def saturPlus(self, args = None, kwargs = None):
        self.saturWasPressed = 1
    def satutMinus(self, args = None, kwargs = None):
        self.saturWasPressed = -1
    def contrastPlus (self, args=None, kwargs= None):
        self.contrastWasPressed = 1
    def contrastMinus(self, args = None, kwargs = None):
        self.contrastWasPressed = -1

    def brightnessPlus(self, args = None, kwargs = None):
        self.brightnessWasPressed = 1

    def brightnessMinus(self, args = None, kwargs = None):
        self.brightnessWasPressed = -1

    def disconnect_camera(self):
        self.done = True
        self.add_log("Camera is disconnected")
    def disconnect1(self, b):
        self.done = True
        self.add_log("Camera is disconnected")
        return self.connect(True,b)
        pygame.quit()

    def add_log(self, log):
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        now = str(now)
        self.listWidget.addItem(now + " - " + log)
        print(log)

    def connect(self, a = True , b = None):
        if not a :
            self.add_log("Connecting...")
            ip, port, login, password, length = open_config()
            num = self.comboBox.currentIndex()
            self.add_log("IP: " + ip[num])
            self.add_log("Port: " + str(port[num]))
            self.add_log("Login: " + login[num])
            self.add_log("Password: " + password[num])
        else:
            num = b
            self.add_log("Connecting...")
            ip, port, login, password, length = open_config()
            self.add_log("IP: " + ip[num])
            self.add_log("Port: " + str(port[num]))
            self.add_log("Login: " + login[num])
            self.add_log("Password: " + password[num])

        # подключение джойстика
        pygame.init()
        if pygame.joystick.get_init() == 1 and pygame.joystick.get_count() > 0:
            self.add_log("Joystick is connected")
            self.add_log("Number of connected joysticks: " + str(pygame.joystick.get_count()))
        else:
            self.add_log("Joystick is uninitialized or not connected")
            return

        try:
            joystick = pygame.joystick.Joystick(0)  # создаем новый объект joystick с id = 0
        except pygame.error:
            self.add_log("Joystick is uninitialized or not connected")
            pygame.close()
            return

        joystick.init()  # инициализация джойстика
        self.add_log("Joystick system name: " + joystick.get_name())  # вывод имени джойстика
        # есть три попытки для подключения к камере
        mycam = None
        attempts = 3
        while mycam is None:
            self.add_log("Connecting to the camera...")
            try:
                mycam = ONVIFCamera(ip[num], port[num], login[num], password[num])  # инициализация камеры
            except ONVIFError:
                self.add_log("Connection failed")
            attempts -= 1
            if attempts == 0:
                del mycam
                pygame.quit()
                return

        self.add_log("Camera is connected")
        self.connectBtn.setDisabled(True)
        self.disconnectBtn.setEnabled(True)

        media = mycam.create_media_service()  # создание media service
        ptz = mycam.create_ptz_service()  # создание ptz service
        image = mycam.create_imaging_service()  # создание imaging service

        media_profile = media.GetProfiles()[0]  # достаем медиа-профиль камеры

        # достаем ptz configuration options
        request = ptz.create_type('GetConfigurationOptions')
        request.ConfigurationToken = media_profile.PTZConfiguration.token
        ptz_configuration_options = ptz.GetConfigurationOptions(request)
        ptz_configurations_list = ptz.GetConfigurations()
        ptz_configuration = ptz_configurations_list[0]

        # создание запроса continuous move для настройки движения камеры
        request = ptz.create_type('ContinuousMove')
        request.ProfileToken = media_profile.token
        request.Velocity = media_profile.PTZConfiguration.DefaultPTZSpeed  # поиск структуры Velocity
        # преобразование структуры Velocity
        request.Velocity.Zoom.x = 0.0
        request.Velocity.PanTilt.space = ''
        request.Velocity.Zoom.space = ''
        ptz.Stop({'ProfileToken': media_profile.token})  # остановка камеры на случай, если она двигалась

        # создание запроса set preset для сохранения пресетов камеры
        prequest = ptz.create_type('SetPreset')
        prequest.ProfileToken = media_profile.token

        # создание запроса go to preset для перехода между пресетами камеры
        grequest = ptz.create_type('GotoPreset')
        grequest.ProfileToken = media_profile.token

        # создание запроса set configuration для настройки скорости движения камеры
        srequest = ptz.create_type('SetConfiguration')

        # создание запроса set imaging settings для настройки изображения с камеры
        irequest = image.create_type('SetImagingSettings')
        video_token = media.GetVideoSourceConfigurationOptions().VideoSourceTokensAvailable[0]
        img_settings = image.GetImagingSettings(video_token)

        global XMAX, XMIN, YMAX, YMIN, ZMAX, ZMIN

        # получение числового диапазона осей X, Y, Z
        XMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
        XMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
        YMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
        YMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min
        ZMAX = ptz_configuration_options.Spaces.ContinuousZoomVelocitySpace[0].XRange.Max
        ZMIN = ptz_configuration_options.Spaces.ContinuousZoomVelocitySpace[0].XRange.Min

        s = -1
        while s < 1:
        	print("%2g maps to %g" % (s, maprange((-1, 1), (XMIN, XMAX), s)))
        	s += 0.1

        global throttle

        isMoving = False
        OX = False
        OY = False
        OZ = False

        self.done = False


        while not self.done:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True

            throttle = (-(joystick.get_axis(THR_AXIS))) / 2 + 0.5
            thread = threading.Thread(target=midi.run, args=())
            thread.daemon = True
            thread.start()

            ptz_configuration.DefaultPTZSpeed.PanTilt.x = throttle * XMAX
            ptz_configuration.DefaultPTZSpeed.PanTilt.y = throttle * YMAX
            ptz_configuration.DefaultPTZSpeed.Zoom.x = throttle * ZMAX

            srequest.PTZConfiguration = ptz_configuration
            srequest.ForcePersistence = False

            ptz.SetConfiguration(srequest)

            grequest.Speed = ptz_configuration.DefaultPTZSpeed
            grequest.Speed.PanTilt.x = throttle
            grequest.Speed.PanTilt.y = throttle
            grequest.Speed.Zoom.x = throttle

            irequest.VideoSourceToken = video_token
            irequest.ImagingSettings = img_settings
            irequest.ForcePersistence = False

            if joystick.get_axis(X_AXIS) > 0.1 or joystick.get_axis(X_AXIS) < -0.1:
                move_horizontal(ptz, request, joystick)
                print(str(maprange((-1, 1), (XMIN, XMAX), joystick.get_axis(X_AXIS))))
                isMoving = True
                OX = True

            if joystick.get_axis(Y_AXIS) > 0.2 or joystick.get_axis(Y_AXIS) < -0.2:
                move_vertical(ptz, request, joystick)
                print(str(maprange((-1, 1), (YMIN, YMAX), joystick.get_axis(Y_AXIS))))
                isMoving = True
                OY = True

            if joystick.get_axis(Z_AXIS) > 0.3 or joystick.get_axis(Z_AXIS) < -0.3:
                zoom(ptz, request, joystick)
                print(str(maprange((-1, 1), (ZMIN, ZMAX), joystick.get_axis(Z_AXIS))))
                isMoving = True
                OZ = True

            if isMoving:

                if -0.1 <= joystick.get_axis(X_AXIS) <= 0.1 and OX:
                    ptz.Stop({'ProfileToken': request.ProfileToken})
                    isMoving = False
                    OX = False

                if -0.2 <= joystick.get_axis(Y_AXIS) <= 0.2 and OY:
                    ptz.Stop({'ProfileToken': request.ProfileToken})
                    isMoving = False
                    OY = False

                if -0.3 <= joystick.get_axis(Z_AXIS) <= 0.3 and OZ:
                    ptz.Stop({'ProfileToken': request.ProfileToken})
                    isMoving = False
                    OZ = False

            ptz = mycam.create_ptz_service()
            if joystick.get_button(6):
                self.disconnect1(2)
            if joystick.get_button(7):
                self.disconnect1(4)
            if joystick.get_button(0) == 1:
                if self.focusMode:
                    self.focusMode = False
                    self.add_log("Entering Brightness / Contrast mode...")
                else:
                    self.focusMode = True
                    self.add_log("Entering Focus mode...")

            if joystick.get_button(2) == 1:

                if self.preset1 == 1:
                    prequest.PresetName = "1"
                    prequest.PresetToken = '1'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #1...")
                    self.preset1 = 0

                if self.preset2 == 1:
                    prequest.PresetName = "2"
                    prequest.PresetToken = '2'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #2...")
                    self.preset2 = 0

                if self.preset3 == 1:
                    prequest.PresetName = "3"
                    prequest.PresetToken = '3'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #3...")
                    self.preset3 = 0
                if self.preset4 == 1:
                    prequest.PresetName = "4"
                    prequest.PresetToken = '4'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #4...")
                    self.preset4 = 0
                if self.preset5 == 1:
                    prequest.PresetName = "5"
                    prequest.PresetToken = '5'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #5...")
                    self.preset5 = 0
                if self.preset6 == 1:
                    prequest.PresetName = "6"
                    prequest.PresetToken = '6'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #6...")
                    self.preset6 = 0
                if self.preset7 == 1:
                    prequest.PresetName = "7"
                    prequest.PresetToken = '7'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #7...")
                    self.preset7 = 0
                if self.preset8 == 1:
                    prequest.PresetName = "8"
                    prequest.PresetToken = '8'
                    preset = ptz.SetPreset(prequest)
                    self.add_log("Setting preset #8...")
                    self.preset8 = 0

            if self.preset1 == 1:
                grequest.PresetToken = '1'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #1...")
                self.preset1=0
            if self.preset2 == 1:
                grequest.PresetToken = '2'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #2...")
                self.preset2 = 0
            if self.preset3 == 1:
                grequest.PresetToken = '3'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #3...")
                self.preset3= 0

            if self.preset4 == 1:
                grequest.PresetToken = '4'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #4...")
                self.preset4 = 0

            if self.preset5 == 1:
                grequest.PresetToken = '5'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #5...")
                self.preset5 = 0

            if self.preset6 == 1:
                grequest.PresetToken = '6'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #6...")
                self.preset6 = 0

            if self.preset7 == 1:
                grequest.PresetToken = '7'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #7...")
                self.preset7 = 0

            if self.preset8 == 1:
                grequest.PresetToken = '8'
                ptz.GotoPreset(grequest)
                self.add_log("Going to preset #8...")
                self.preset8 = 0

            # настройка изображения

            if not self.focusMode:
                # увеличение яркости (6 кнопка)
                if self.brightnessWasPressed == 1:
                    if img_settings.Brightness < 100:
                        img_settings.Brightness += 10
                        if img_settings.Brightness > 100:
                            img_settings.Brightness = 100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing brightness to " + str(img_settings.Brightness) + "...")
                    print("Increasing brightness to {}".format(img_settings.Brightness))
                    self.brightnessWasPressed = 0

                # уменьшение яркости (4 кнопка)
                if self.brightnessWasPressed == -1:
                    if img_settings.Brightness > 0:
                        img_settings.Brightness -= 10
                        if img_settings.Brightness < 0:
                            img_settings.Brightness = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing brightness to " + str(img_settings.Brightness) + "...")
                    print("reducing brightness to {}".format(img_settings.Brightness))
                    self.brightnessWasPressed = 0
                #увеличение резкости
                if self.sharpnessWasPressed == 1:
                    if img_settings.Sharpness < 100:
                        img_settings.Sharpness += 10
                        if img_settings.Sharpness > 100:
                            img_settings.Sharpness = 100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing sharpness to " + str(img_settings.Sharpness) + "...")
                    print("Increasing sharpness to {}".format(img_settings.Sharpness))
                    self.sharpnessWasPressed = 0
                #уменьшение резкости
                if self.sharpnessWasPressed == -1:
                    if img_settings.Sharpness > 0:
                        img_settings.Sharpness -= 10
                        if img_settings.Sharpness < 0:
                            img_settings.Sharpness = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing sharpness to " + str(img_settings.Sharpness) + "...")
                    print("Reducing sharpness to {}".format(img_settings.Sharpness))
                    self.sharpnessWasPressed = 0
                #увеличение насыщености
                if self.saturWasPressed == 1:
                    if img_settings.ColorSaturation <100:
                        img_settings.ColorSaturation += 10
                        if img_settings.ColorSaturation>100:
                            img_settings.ColorSaturation=100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing Color Saturation to " + str(img_settings.ColorSaturation) + "...")
                    print("Increasing Color Saturation to {}".format(img_settings.ColorSaturation))
                    self.saturWasPressed = 0
                #уменьшение насыщености
                if self.saturWasPressed == -1:
                    if img_settings.ColorSaturation > 0:
                        img_settings.ColorSaturation -= 10
                        if img_settings.ColorSaturation < 0:
                            img_settings.ColorSaturation = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing Color Saturation to " + str(img_settings.ColorSaturation) + "...")
                    print("Reducing Color Saturation to {}".format(img_settings.ColorSaturation))
                    self.saturWasPressed = 0
                # увеличение контрастности (5 кнопка)
                if self.contrastWasPressed == 1:
                    if img_settings.Contrast < 100:
                        img_settings.Contrast += 10
                        if img_settings.Contrast > 100:
                            img_settings.Contrast = 100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing contrast to " + str(img_settings.Contrast) + "...")
                    self.contrastWasPressed = 0

                # уменьшение контрастности (3 кнопка)
                if self.contrastWasPressed == -1:
                    if img_settings.Contrast > 0:
                        img_settings.Contrast -= 10
                        if img_settings.Contrast < 0:
                            img_settings.Contrast = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing contrast to " + str(img_settings.Contrast) + "...")
                    self.contrastWasPressed = 0
            else:
                # включение автофокуса (6 кнопка)
                if joystick.get_button(5) == 1:
                    img_settings.Focus.AutoFocusMode = 'AUTO'
                    self.add_log("Turning on AUTO focus...")

                # включение ручного фокуса (5 кнопка)
                if joystick.get_button(4) == 1:
                    img_settings.Focus.AutoFocusMode = 'MANUAL'
                    self.add_log("Turning on MANUAL focus...")
                irequest.ImagingSettings = img_settings
                image.SetImagingSettings(irequest)

            # переключение режима цветового баланса
            if joystick.get_button(1) == 1:
                img_settings = image.GetImagingSettings(video_token)
                if img_settings.WhiteBalance.Mode == 'AUTO':
                    img_settings.WhiteBalance.Mode = 'MANUAL'
                    self.add_log("Switching to MANUAL white balance mode...")
                    img_settings.WhiteBalance.CbGain = 80  # оптимальные настройки CbGain
                    img_settings.WhiteBalance.CrGain = 30  # оптимальные настройки CrGain
                else:
                    img_settings.WhiteBalance.Mode = 'AUTO'
                    self.add_log("Switching to AUTO white balance mode...")
                irequest.ImagingSettings = img_settings
                image.SetImagingSettings(irequest)
                img_settings = image.GetImagingSettings(video_token)

            if img_settings.WhiteBalance.Mode == 'MANUAL':

                # увеличение CbGain
                if joystick.get_hat(0) == (1, 0):
                    if img_settings.WhiteBalance.CbGain < 100:
                        img_settings.WhiteBalance.CbGain += 5
                        if img_settings.WhiteBalance.CbGain > 100:
                            img_settings.WhiteBalance.CbGain = 100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing CbGain to " + str(img_settings.WhiteBalance.CbGain) + "...")

                # уменьшение CbGain
                if joystick.get_hat(0) == (-1, 0):
                    if img_settings.WhiteBalance.CbGain > 0:
                        img_settings.WhiteBalance.CbGain -= 5
                        if img_settings.WhiteBalance.CbGain < 0:
                            img_settings.WhiteBalance.CbGain = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing CbGain to " + str(img_settings.WhiteBalance.CbGain) + "...")

                # увеличение CrGain
                if joystick.get_hat(0) == (0, 1):
                    if img_settings.WhiteBalance.CrGain < 100:
                        img_settings.WhiteBalance.CrGain += 5
                        if img_settings.WhiteBalance.CrGain > 100:
                            img_settings.WhiteBalance.CrGain = 100
                    image.SetImagingSettings(irequest)
                    self.add_log("Increasing CrGain to " + str(img_settings.WhiteBalance.CrGain) + "...")

                # уменьшение CrGain
                if joystick.get_hat(0) == (0, -1):
                    if img_settings.WhiteBalance.CrGain > 0:
                        img_settings.WhiteBalance.CrGain -= 5
                        if img_settings.WhiteBalance.CrGain < 0:
                            img_settings.WhiteBalance.CrGain = 0
                    image.SetImagingSettings(irequest)
                    self.add_log("Reducing CrGain to " + str(img_settings.WhiteBalance.CrGain) + "...")

            self.listWidget.scrollToBottom()

        del mycam
        self.connectBtn.setEnabled(True)
        self.disconnectBtn.setDisabled(True)
        pygame.quit()


# мапинг значений осей
def maprange(a, b, s):
	(a1, a2), (b1, b2) = a, b
	return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))


# считывание данных о камере из текстового файла
def open_config():
    file = open("config.txt", "r")
    length = file_length(file)
    length /= 4
    file = open("config.txt", "r")
    num = 0
    ip = {}
    port = {}
    login = {}
    password = {}
    while num < length:
        temp = file.readline().split("\n")
        ip[num] = temp[0]

        temp = (file.readline().split("\n"))
        port[num] = int(temp[0])

        temp = file.readline().split("\n")
        login[num] = temp[0]

        temp = file.readline().split("\n")
        password[num] = temp[0]

        num += 1

    file.close()

    return ip, port, login, password, length


# подсчет длины файла
def file_length(file):
    lines = 0
    for line in file:
        lines += 1
    file.close()
    return lines


def find_key(dict, value):
    return [k for k, v in dict.iteritems() if v == value][0]


# движение камеры по горизонтали
def move_horizontal(ptz, request, joystick):
    request.Velocity.PanTilt.x = maprange((-1, 1), (XMIN, XMAX), joystick.get_axis(X_AXIS))
    request.Velocity.PanTilt.y = 0
    request.Velocity.Zoom.x = 0
    ptz.ContinuousMove(request)


# движение камеры по вертикали
def move_vertical(ptz, request, joystick):
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = maprange((-1, 1), (YMIN, YMAX), joystick.get_axis(Y_AXIS))
    request.Velocity.Zoom.x = 0
    ptz.ContinuousMove(request)


# зумирование
def zoom(ptz, request, joystick):
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = 0
    request.Velocity.Zoom.x = maprange((-1, 1), (ZMIN, ZMAX), joystick.get_axis(Z_AXIS))
    ptz.ContinuousMove(request)


def main():
    zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue  # нужно для корректной работы камеры

    qt_app = QtWidgets.QApplication(sys.argv)  # новый экземпляр QApplication
    window = Application()  # создаём объект класса Application

    window.show()  # показываем окно
    window.disconnectBtn.setDisabled(True)
    ip, port, login, password, length = open_config()
    num = 0
    midi.map_pad_press(window.brightnessPlus,1)
    midi.map_pad_press(window.contrastPlus,2)
    midi.map_pad_press(window.sharpnessPlus, 3)
    midi.map_pad_press(window.saturPlus, 4)
    midi.map_pad_press(window.brightnessMinus,9)
    midi.map_pad_press(window.contrastMinus, 10)
    midi.map_pad_press(window.sharpnessMinus, 11)
    midi.map_pad_press(window.satutMinus, 12)

    midi.map_pad_press(window.preset1ch,5)
    midi.map_pad_press(window.preset2ch, 6)
    midi.map_pad_press(window.preset3ch, 7)
    midi.map_pad_press(window.preset4ch, 8)
    midi.map_pad_press(window.preset5ch, 13)
    midi.map_pad_press(window.preset6ch, 14)
    midi.map_pad_press(window.preset7ch, 15)
    midi.map_pad_press(window.preset8ch, 16)
    while num < length:
        window.comboBox.addItem(ip[num])
        num += 1
    qt_app.exec_()  # запускаем приложение


if __name__ == '__main__':  # если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
