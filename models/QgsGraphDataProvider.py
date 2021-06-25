from qgis.core import *

import traceback

class QgsGraphFeatureIterator(QgsAbstractFeatureIterator):

    def __init__(self, source, request=QgsFeatureRequest()):
        super().__init__(request)

        self._request = request
        self._source = source
        self._index = 0

    def fetchFeature(self, feat):
        """Gets actually looked at feature. Increases feature index for next fetchFeature.

        Args:
            feat ([type]): Feature to be filled with information from fetched feature.

        Returns:
            [type]: True if successfull
        """
        # TODO this is a very simplified version of fetchFeature (e.g. request completely ignored -> necessary?)
        if self._index == len(self._source._features):
            return False
        
        try:
            _feat = self._source._features[self._index]
            feat.setGeometry(_feat.geometry())
            feat.setFields(_feat.fields())
            feat.setAttributes(_feat.attributes())
            feat.setValid(_feat.isValid())
            feat.setId(_feat.id())

            self._index += 1

            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):        
        if self._index + 1 < len(self._source._features):
            self._index += 1
        
        return self._source._features[self._index]

    def rewind(self):
        self._index = 0
        return True

    def close(self):
        self._index = -1
        return True


class QgsGraphFeatureSource(QgsAbstractFeatureSource):

    def __init__(self, provider):
        super(QgsGraphFeatureSource).__init__()

        self._provider = provider
        self._features = provider._features

    def getFeatures(self, request):
        return QgsFeatureIterator(QgsGraphFeatureIterator(self, request))


class QgsGraphDataProvider(QgsVectorDataProvider):
    """Data provider for GraphLayer

    Args:
        QgsVectorDataProvider ([type]): Extends QgsVectorDataProvider to be able to store fields and features.
    """

    nextFeatId = 1

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

        tempLayer = QgsVectorLayer(uri, "tmp", "memory")
        self.mCRS = QgsProject.instance().crs()
        
        self._uri = uri
        self._providerOptions = providerOptions
        self._flags = flags
        self._features = []
        self._fields = tempLayer.fields()
        self._extent = QgsRectangle()
        self._subsetString = ''
        self._featureCount = 0

        self._points = True

        # if 'index=yes' in self._uri:
        #     self.createSpatialIndex()

    def isValid(self):
        return True

    def setDataSourceUri(self, uri):
        self._uri = uri

    def dataSourceUri(self, expandAuthConfig=True):
        return self._uri

    def setCrs(self, crs):
        self.mCRS = crs

    def crs(self):
        if self.mCRS == None:
            return QgsProject.instance().crs()

        return self.mCRS

    def featureSource(self):
        return QgsGraphFeatureSource(self)

    def getFeatures(self, request=QgsFeatureRequest()):
        # return self._features
        return QgsFeatureIterator(QgsGraphFeatureIterator(self.featureSource(), request))

    def featureCount(self):
        return self._featureCount

    def fields(self):
        return self._fields

    def addFeature(self, feat, flags=None):
        # TODO check for valid feature

        self._features.append(feat)
        self.nextFeatId += 1
        self._featureCount += 1

        # if self._spatialindex is not None:
        #     self._spatialindex.insertFeatue(feat)

        return True

    def deleteFeature(self, id):
        try:
            del self._features[id]
            self._featureCount -= 1
        
            return True
        except Exception as e:
            # probably index out of bound
            return False

    def addAttributes(self, attrs):
        # TODO check for valid attribute types defined by fields
        for field in attrs:
            self._fields.append(field)
            self._uri += "&field=" + field.displayName() + ":" + field.typeName()

        return True

    def createSpatialIndex(self):
        # TODO?
        pass

    def capabilities(self):
        # how many capabilities to return?
        return QgsVectorDataProvider.AddFeature | QgsVectorDataProvider.AddAttributes

    def subsetString(self):
        return self._subsetString

    def extent(self):
        # TODO this update of extent maybe in addFeature?
        for feat in self._features:
            self._extent.combineExtentWith(feat.geometry().boundingBox())

        return self._extent

    def updateExtents(self):
        # TODO understand this
        self._extent.setMinimal()

    def name(self):
        return self.providerKey()

    def setGeometryToPoint(self, points):
        self._points = points