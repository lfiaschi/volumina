'''Input and output from and to other libraries resp. formats.

Volumine works with 5d array-like objects assuming the coordinate
system (time, x, y, z, channel). This module provides methods to convert other
data types to this expected format.
'''
import os
import os.path as path
import numpy as np
from volumina.slicingtools import sl, slicing2shape
import numpy

_has_vigra = True
try:
    import vigra
except ImportError:
    _has_vigra = False


###
### lazyflow input
###
_has_lazyflow = True
try:
    from lazyflow.graph import Operator, InputSlot, OutputSlot
    from lazyflow.roi import TinyVector
except ImportError:
    _has_lazyflow = False

if _has_lazyflow and _has_vigra:

    class Op5ifyer(Operator):
        name = "Op5ifyer"
        inputSlots = [InputSlot("input"), InputSlot("order", stype='string', optional=True)]
        outputSlots = [OutputSlot("output")]

        def __init__(self, *args, **kwargs):
            super(Op5ifyer, self).__init__(*args, **kwargs)
            
            # By default, use volumina axis order
            self._axisorder = 'txyzc'
                    
        def setupOutputs(self):
            inputAxistags = self.inputs["input"]._axistags
            inputShape = list(self.inputs["input"]._shape)
            self.resSl = [slice(0,stop,None) for stop in list(self.inputs["input"]._shape)]
            
            if self.order.ready():
                self._axisorder = self.order.value

            outputTags = vigra.defaultAxistags( self._axisorder )
            
            for tag in [tag for tag in outputTags if tag not in inputAxistags]:
                #inputAxistags.insert(outputTags.index(tag.key),tag)
                #inputShape.insert(outputTags.index(tag.key),1)
                self.resSl.insert(outputTags.index(tag.key),0)
            
            outputShape = []
            for tag in outputTags:
                if tag in inputAxistags:
                    outputShape += [ inputShape[ inputAxistags.index(tag.key) ] ]
                else:
                    outputShape += [1]                
            
            self.outputs["output"]._dtype = self.inputs["input"]._dtype
            self.outputs["output"]._shape = tuple(outputShape)
            self.outputs["output"]._axistags = outputTags
            
        def execute(self,slot,roi,result):
            
            sl = [slice(0,roi.stop[i]-roi.start[i],None) if sl != 0\
                  else slice(0,1) for i,sl in enumerate(self.resSl)]
            
            inputTags = self.input.meta.axistags
            
            # Convert the requested slice into a slice for our input
            outSlice = roi.toSlice()
            inSlice = [None] * len(inputTags)
            for i, s in enumerate(outSlice):
                tagKey = self.output.meta.axistags[i].key
                inputAxisIndex = inputTags.index(tagKey)
                if inputAxisIndex < len(inputTags):
                    inSlice[inputAxisIndex] = s

            tmpres = self.inputs["input"][inSlice].wait()
            
            # Re-order the axis the way volumina expects them
            v = tmpres.view(vigra.VigraArray)
            v.axistags = inputTags
            result[sl] = v.withAxes(*list( self._axisorder ))
        
        def notifyDirty(self, inputSlot, key):
            if inputSlot.name == 'input':
                # Convert the key into an output key
                inputTags = [tag.key for tag in self.input.meta.axistags]
                taggedKey = {k:v for (k,v) in zip(inputTags, key) }

                outKey = []
                outputTags = [tag.key for tag in self.output.meta.axistags]
                for tag in outputTags:
                    if tag in taggedKey.keys():
                        outKey += [taggedKey[tag]]
                    else:
                        outKey += [slice(None)]
                
                self.output.setDirty(outKey)                
            elif inputSlot.name == 'order':
                self.output.setDirty(slice(None))
            else:
                assert False, "Unknown input"
    
    class OpChannelSelector(Operator):
        name = 'OpChannelSelector'
        inputSlots = [InputSlot("Input"), InputSlot("Channel")]
        outputSlots = [OutputSlot("Output")]
        
        def __init__(self, *args, **kwargs):
            super(OpChannelSelector, self).__init__(*args, **kwargs)
            
                    
        def setupOutputs(self):
            inputSlot = self.inputs["Input"]
            outputSlot = self.outputs["Output"]
            outputSlot.meta.assignFrom(inputSlot.meta)
            outputSlot.meta.shape = tuple([1 if inputSlot.meta.axistags.channelIndex == i else \
                                          inputSlot.meta.shape[i] for i in range(len(inputSlot.meta.shape))])
            
        def execute(self,slot,roi,result):
            c = self.inputs["Channel"].value
            inputSlot = self.inputs["Input"]
            roi.start = [c if i==inputSlot.meta.axistags.channelIndex else roi.start[i] \
                         for i in range(len(roi.start))]
            roi.stop = [c+1 if i==inputSlot.meta.axistags.channelIndex else roi.stop[i] \
                         for i in range(len(roi.stop))]
            result[:] = self.inputs["Input"](roi.start,roi.stop).wait()
            

class Array5d( object ):
    '''Embed a array with dim = 3 into the volumina coordinate system.'''
    def __init__( self, array, dtype=np.uint8):
        assert(len(array.shape) == 3)
        self.a = array
        self.dtype=dtype
        
    def __getitem__( self, slicing ):
        sl3d = (slicing[1], slicing[2], slicing[3])
        ret = np.zeros(slicing2shape(slicing), dtype=self.dtype)
        ret[0,:,:,:,0] = self.a[tuple(sl3d)]
        return ret
    @property
    def shape( self ):
        return (1,) + self.a.shape + (1,)

    def astype( self, dtype):
        return Array5d( self.a, dtype )

if __name__ == "__main__":
    
    import vigra
    from lazyflow.graph import Graph
    
    g = Graph()
    op = OpChannelSelector(g)
    v = vigra.VigraArray((10,10,10))
    
    op.inputs["Input"].setValue(v)
    op.inputs["Channel"].setValue(3)
    
    print op.outputs["Output"]().wait().shape
