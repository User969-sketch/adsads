import configparser


class Configs(configparser.ConfigParser):
    def __init__(self, filename='configs.ini'):
        configparser.ConfigParser.__init__(self)
        self.read(filename)
        self.configs = {}

    def getConfigs(self):
        for configStoreName in list(self.keys()):
            self.configs[configStoreName] = {}

            for configName in list(self[configStoreName].keys()):
                self.configs[configStoreName][configName] = self[configStoreName][configName]

        return self