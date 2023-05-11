import os
import threading

import configs
import server


def main():
    import adds
    
    Configs = configs.Configs(filename='configs.ini').getConfigs()
    Server = server.MainApp(Configs.configs)

    Server.start()

if __name__ == '__main__': main()