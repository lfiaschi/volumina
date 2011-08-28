from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QColor

#*******************************************************************************
# L a y e r                                                                    *
#*******************************************************************************

class Layer( QObject ):
    '''
    Entries of a LayerStackModel,
    which is in turn displayed to the user via a LayerStackWidget
    
    properties:
    datasources -- list of ArraySourceABC; read-only
    visible -- boolean
    opacity -- float; range 0.0 - 1.0

    '''
    visibleChanged = pyqtSignal(bool)
    opacityChanged = pyqtSignal(float)

    @property
    def visible( self ):
        return self._visible
    @visible.setter
    def visible( self, value ):
        if value != self._visible:
            self._visible = value
            self.visibleChanged.emit( value )

    @property
    def opacity( self ):
        return self._opacity
    @opacity.setter
    def opacity( self, value ):
        if value != self._opacity:
            self._opacity = value
            self.opacityChanged.emit( value )

    @property
    def datasources( self ):
        return self._datasources

    def contextMenu(self, parent, pos):
        print "no context menu implemented"

    def __init__( self, opacity = 1.0, visible = True ):
        super(Layer, self).__init__()
        self.name    = "Unnamed Layer"
        self.mode = "ReadOnly"
        self._visible = visible
        self._opacity = opacity


#*******************************************************************************
# G r a y s c a l e L a y e r                                                  *
#*******************************************************************************

class GrayscaleLayer( Layer ):
    thresholdingChanged = pyqtSignal(int, int)
    
    def __init__( self, datasource, thresholding = None ):
        super(GrayscaleLayer, self).__init__()
        self._datasources = [datasource]
        self._thresholding = thresholding
    @property
    def thresholding(self):
        """returns a tuple witht the range [minimum value, maximum value]"""
        return self._thresholding
    @thresholding.setter
    def thresholding(self, t):
        self._thresholding = t
        self.thresholdingChanged.emit(t[0], t[1])
    
    def contextMenu(self, parent, pos):
        from widgets.layerDialog import GrayscaleLayerDialog
        from PyQt4.QtGui import QMenu, QAction
         
        menu = QMenu("Menu", parent)
        
        title = QAction("%s" % self.name, menu)
        title.setEnabled(False)
        menu.addAction(title)
        menu.addSeparator()
        
        adjThresholdAction = QAction("Adjust thresholds", menu)
        menu.addAction(adjThresholdAction)

        ret = menu.exec_(pos)
        if ret == adjThresholdAction:
            
            dlg = GrayscaleLayerDialog(parent)
            dlg.setLayername(self.name)
            def dbgPrint(a, b):
                self.thresholding = (a,b)
                print "range changed to [%d, %d]" % (a,b)
            dlg.grayChannelThresholdingWidget.rangeChanged.connect(dbgPrint)
            dlg.show()

#*******************************************************************************
# A l p h a M o d u l a t e d L a y e r                                        *
#*******************************************************************************

class AlphaModulatedLayer( Layer ):
    def __init__( self, datasource, tintColor = QColor(255,0,0), normalize = None ):
        super(AlphaModulatedLayer, self).__init__()
        self._datasources = [datasource]
        self._normalize = normalize
        self.tintColor = tintColor

#*******************************************************************************
# C o l o r t a b l e L a y e r                                                *
#*******************************************************************************

class ColortableLayer( Layer ):
    def __init__( self, datasource , colorTable):
        super(ColortableLayer, self).__init__()
        self._datasources = [datasource]
        self.colorTable = colorTable


#*******************************************************************************
# R G B A L a y e r                                                            *
#*******************************************************************************

class RGBALayer( Layer ):
    @property
    def color_missing_value( self ):
        return self._color_missing_value

    @property
    def alpha_missing_value( self ):
        return self._alpha_missing_value

    def __init__( self, red = None, green = None, blue = None, alpha = None, \
                  color_missing_value = 0, alpha_missing_value = 255,
                  normalizeR=None, normalizeG=None, normalizeB=None, normalizeA=None):
        super(RGBALayer, self).__init__()
        self._datasources = [red,green,blue,alpha]
        self._normalize   = [normalizeR, normalizeG, normalizeB, normalizeA]
        self._color_missing_value = color_missing_value
        self._alpha_missing_value = alpha_missing_value
