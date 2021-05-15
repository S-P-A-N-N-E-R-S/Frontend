""" Basic helper functions """

from os.path import abspath, join, dirname


def getPluginPath():
    """ Get the absolute path to plugin root folder"""
    return abspath(dirname(__file__))


def getImagePath(image):
    """ Get the image path """
    path = join(getPluginPath(), "resources/images")
    return abspath(join(path, image))

def getExamplePath(example):
    """ Get the example path """
    path = join(getPluginPath(), "resources/examples")
    return abspath(join(path, example))
