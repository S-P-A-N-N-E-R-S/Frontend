from qgis.core import *

import traceback

class QgsGraphFeatureIterator(QgsAbstractFeatureIterator):

    def __init__(self, source, point, request=QgsFeatureRequest()):
        super().__init__(request)
        self._request = request
        self._source = source
        self._index = 0
        self._pointKeys = list(self._source._pointFeatures.keys())
        self._lineKeys = list(self._source._lineFeatures.keys())

        self.point = point

    def __del__(self):
        del self._pointKeys
        del self._lineKeys
        del self._request

    def isValid(self):
        return True

    def fetchFeature(self, feat):
        """
        Gets actually looked at feature. Increases feature index for next fetchFeature.

        :type feat: QgsFeature to be filled with information from fetched feature.
        :return Boolean If fetch was successful
        """
        # TODO this is a very simplified version of fetchFeature (e.g. request completely ignored -> necessary?)
        if self.point:
            # point feature at index
            if self._index >= len(self._source._pointFeatures):
                return False

            featIdx = self._pointKeys[self._index]
            _feat = self._source._pointFeatures[featIdx]
            feat.setGeometry(_feat.geometry())
            feat.setFields(_feat.fields())
            feat.setAttributes(_feat.attributes())
            feat.setValid(_feat.isValid())
            feat.setId(_feat.id())
        else:
            # line feature at index
            if self._index >= len(self._source._lineFeatures):
                return False

            featIdx = self._lineKeys[self._index]
            _feat = self._source._lineFeatures[featIdx]
            feat.setGeometry(_feat.geometry())
            feat.setFields(_feat.fields())
            feat.setAttributes(_feat.attributes())
            feat.setValid(_feat.isValid())
            feat.setId(_feat.id())

        self._index += 1

        return True

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self.point:
            if self._index + 1 < len(self._source._pointFeatures):
                self._index += 1
            return self._source._pointFeatures[self._pointKeys[self._index]]
        
        else:
            if self._index + 1 < len(self._source._lineFeatures):
                self._index += 1
            return self._source._lineFeatures[self._lineKeys[self._index]]

    def rewind(self):
        self._pointKeys = list(self._source._pointFeatures.keys())
        self._lineKeys = list(self._source._lineFeatures.keys())
        self._index = 0
        return True

    def close(self):
        self._pointKeys = []
        self._lineKeys = []
        self._index = -1
        return True


class QgsGraphFeatureSource(QgsAbstractFeatureSource):

    def __init__(self, provider, point):
        super(QgsGraphFeatureSource).__init__()
        self._provider = provider
        self._pointFeatures = provider._pointFeatures
        self._lineFeatures = provider._lineFeatures
        
        self.point = point

    def __del__(self):
        pass

    def getFeatures(self, request, point):
        return QgsFeatureIterator(QgsGraphFeatureIterator(self, request, point))


class QgsGraphDataProvider(QgsVectorDataProvider):
    """
    DataProvider for GraphLayer
    Keeps track of features for PointGeometry AND LineGeometry
    """

    @classmethod
    def providerKey(self):
        return "graphprovider"

    @classmethod
    def description(self):
        return "DataProvider for QgsGraphLayer"

    @classmethod
    def createProvider(self, uri='', providerOptions=QgsDataProvider.ProviderOptions(), flags=QgsDataProvider.ReadFlags()):
        return QgsGraphDataProvider(uri, providerOptions, flags)

    
    def __init__(self, uri='', providerOptions=QgsDataProvider.ProviderOptions(), flags=QgsDataProvider.ReadFlags()):
        super().__init__(uri)

        self.mCRS = QgsProject.instance().crs()
        
        self._pointUri = uri
        self._lineUri = uri
        
        self._providerOptions = providerOptions
        self._flags = flags
        
        self._pointFeatures = {}
        self._lineFeatures = {}
        
        self._pointFields = QgsFields()
        self._lineFields = QgsFields()
        
        self._extent = QgsRectangle()
        self._subsetString = ''
        
        self._pointFeatureCount = 0
        self._lineFeatureCount = 0

        self._points = True # if graph has only points

        # if 'index=yes' in self._uri:
        #     self.createSpatialIndex()

    def __del__(self):
        del self._pointFeatures
        del self._lineFeatures
        del self._pointFields
        del self._lineFields
        del self._extent
        del self._providerOptions
        
    def isValid(self):
        return True

    def setDataSourceUri(self, uri, point):
        if point:
            self._pointUri = uri
        else:
            self._lineUri = uri

    def dataSourceUri(self, point, expandAuthConfig=True):
        if point:
            return self._pointUri
        else:
            return self._lineUri

    def setCrs(self, crs):
        self.mCRS = crs

    def crs(self):
        if self.mCRS == None:
            return QgsProject.instance().crs()

        return self.mCRS

    def featureSource(self, point):
        return QgsGraphFeatureSource(self, point)

    def getFeatures(self, point, request=QgsFeatureRequest()):
        # return self._pointFeatures and self._lineFeatures one by one in a tuple
        return QgsFeatureIterator(QgsGraphFeatureIterator(self.featureSource(point), point, request))

    def featureCount(self, point):
        if point:
            return self._pointFeatureCount
        else:
            return self._lineFeatureCount

    def fields(self, point):
        if point:
            return self._pointFields
        else:
            return self._lineFields

    def addFeature(self, feat, point, flags=None):
        """
        Adds a feature to the data provider

        :type feat: QgsFeature
        :type point: Bool True if added feature is point feature, False if feature is line feature
        :type flags: ...
        :return True
        """
        if point:
            self._pointFeatures[feat.attribute(0)] = feat
            self._pointFeatureCount += 1
        else:
            self._lineFeatures[feat.attribute(0)] = feat
            self._lineFeatureCount += 1

        # if self._spatialindex is not None:
        #     self._spatialindex.insertFeatue(feat)

        return True

    def deleteFeature(self, id, point):
        if point and id in self._pointFeatures:
            del self._pointFeatures[id]
            self._pointFeatureCount -= 1
        
            return True
        elif not point and id in self._lineFeatures:
            del self._lineFeatures[id]
            self._lineFeatureCount -= 1

            return True
        return False

    def addAttributes(self, attrs, point):
        if point:
            for field in attrs:
                self._pointFields.append(field)
                self._pointUri += "&field=" + field.displayName() + ":" + field.typeName()
        else:
            for field in attrs:
                self._lineFields.append(field)
                self._lineUri += "&field=" + field.displayName() + ":" + field.typeName()

        return True

    def createSpatialIndex(self):
        # TODO?
        pass

    def capabilities(self):
        # how many capabilities to return?
        return QgsVectorDataProvider.AddFeature | QgsVectorDataProvider.AddAttributes

    def subsetString(self):
        return self._subsetString

    def updateExtents(self):
        # TODO understand this
        self._extent.setMinimal()

    def name(self):
        return self.providerKey()

    def setGeometryToPoint(self, points):
        self._points = points