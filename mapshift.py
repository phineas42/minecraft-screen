#!/usr/bin/python
import sys, re
from struct import *
# from enum import Enum
from collections import namedtuple
from pprint import *
import gzip
import numpy as np
from PIL import Image

NBTID_dict  = dict((v,k) for k,v in enumerate([
  'End', # = 0
  'Byte', # = 1
  'Short', # = 2
  'Int', # = 3
  'Long', # = 4
  'Float', # = 5
  'Double', # = 6
  'Byte_Array', # = 7
  'String', # = 8
  'List', # = 9
  'Compound', # = 10
  'Int_Array', # = 11
]))

NBTID = namedtuple('NBTID', NBTID_dict.keys())(**NBTID_dict)

BaseColors=[
  (0,0,0),
  (125,176,55),
  (244,230,161),
  (197,197,197),
  (252,0,0),
  (158,158,252),
  (165,165,165),
  (0,123,0),
  (252,252,252),
  (162,166,182),
  (149,108,76),
  (111,111,111),
  (63,63,252),
  (141,118,71),
  (252,249,242),
  (213,125,50),
  (176,75,213),
  (101,151,213),
  (226,226,50),
  (125,202,25),
  (239,125,163),
  (75,75,75),
  (151,151,151),
  (75,125,151),
  (125,62,176),
  (50,75,176),
  (101,75,50),
  (101,125,50),
  (151,50,50),
  (25,25,25),
  (247,235,76),
  (91,216,210),
  (73,129,252),
  (0,214,57),
  (127,85,48),
  (111,2,0),
  (126,84,48)
]

Colors=[
[tuple(int(round(float(e)*180/255)) for e in BaseColor),
      tuple(int(round(float(e)*220/255)) for e in BaseColor),
      BaseColor,
      tuple(int(round(float(e)*135/255)) for e in BaseColor)] for BaseColor in BaseColors
]
Palette=np.asarray(Colors).ravel().copy()
Palette.resize(768,)

class NBT:
  @staticmethod
  def parse(nbt_data):
    nbt, bytes_read = NBT.read_nbt(nbt_data)
    return nbt

  @staticmethod
  def unpack(fmt,data,offset):
    result = None
    try:
      result, = unpack_from(fmt,data,offset)
    except ValueError:
      pass
    return result

  @staticmethod
  def read_nbt(nbt_data,offset=0):
    bytes_read = 0
    nbt_id = NBT.unpack('>B',nbt_data,offset+bytes_read)
    bytes_read += 1
    if nbt_id == NBTID.End:
      nbt_name=None
    else:
      name_length = NBT.unpack('>H',nbt_data,offset+bytes_read)
      bytes_read += 2
      nbt_name = NBT.unpack('>%ds'%name_length,nbt_data,offset+bytes_read)
      bytes_read += name_length
    nbt_payload,nbt_payload_bytes = NBT.read_payload(nbt_id,nbt_data,offset+bytes_read)
    bytes_read += nbt_payload_bytes
    return NBT(nbt_id,nbt_name,nbt_payload), bytes_read

  @staticmethod
  def read_payload(nbt_id,nbt_data,offset=0):
    bytes_read = 0
    if nbt_id == NBTID.End:
      nbt_payload = None
    elif nbt_id == NBTID.Byte:
      nbt_payload, = unpack_from('>B',nbt_data,offset+bytes_read)
      bytes_read += 1
    elif nbt_id == NBTID.Short:
      nbt_payload, = unpack_from('>h',nbt_data,offset+bytes_read)
      bytes_read += 2
    elif nbt_id == NBTID.Int:
      nbt_payload, = unpack_from('>i',nbt_data,offset+bytes_read)
      bytes_read += 4
    elif nbt_id == NBTID.Long:
      nbt_payload, = unpack_from('>q',nbt_data,offset+bytes_read)
      bytes_read += 8
    elif nbt_id == NBTID.Float:
      nbt_payload, = unpack_from('>f',nbt_data,offset+bytes_read)
      bytes_read += 4
    elif nbt_id == NBTID.Double:
      nbt_payload, = unpack_from('>d',nbt_data,offset+bytes_read)
      bytes_read += 8
    elif nbt_id == NBTID.Byte_Array:
      payload_size, = unpack_from('>i',nbt_data,offset+bytes_read)
      bytes_read += 4
      nbt_payload = unpack_from('>%dB'%payload_size,nbt_data,offset+bytes_read)
      bytes_read += payload_size * 1
    elif nbt_id == NBTID.String:
      payload_size, = unpack_from('>h',nbt_data,offset+bytes_read)
      bytes_read += 2
      nbt_payload, = unpack_from('>%ds'%payload_size,nbt_data,offset+bytes_read)
      bytes_read += payload_size
    elif nbt_id == NBTID.List:
      payload_type,payload_size = unpack_from('>Bi',nbt_data,offset+bytes_read)
      bytes_read +=5
      nbt_payload = []
      for i in range(0,payload_size):
        child_payload,child_payload_bytes = read_payload(payload_type,nbt_data,offset+bytes_read)
        bytes_read += child_payload_bytes
        nbt_payload.append(NBT(payload_type,'',child_payload))
    elif nbt_id == NBTID.Compound:
      nbt_payload = []
      while True:
        child_nbt,child_bytes = NBT.read_nbt(nbt_data,offset+bytes_read)
        nbt_payload.append(child_nbt)
        bytes_read += child_bytes
        if child_nbt.nbt_id == NBTID.End:
          break
    elif nbt_id == NBTID.Int_Array:
      payload_size, = unpack_from('>i',nbt_data,offset+bytes_read)
      bytes_read +=4
      nbt_payload = unpack_from('>%di'%payload_size,nbt_data,offset+bytes_read)
      bytes_read += payload_size * 4
    else:
      print "Unknown NBT ID: %d"%nbt_id
      exit(-2)
    return nbt_payload, bytes_read
    
  def __init__(self, nbt_id, nbt_name="", nbt_payload=None):
    self.nbt_id = nbt_id
    self.nbt_name = nbt_name or ""
    if nbt_payload is None:
      self.nbt_payload = []
    else:
      self.nbt_payload = nbt_payload
  def __repr__(self):
     if self.nbt_id in [ NBTID.Compound, NBTID.Byte_Array, NBTID.List, NBTID.Int_Array ]:
       payloadstr = " ".join([ child.__repr__() for child in self.nbt_payload ])
     else:
       payloadstr = str(self.nbt_payload)
     return "[ id: %d, name: %s, payload: %s ]"%(self.nbt_id,self.nbt_name,payloadstr)
  def append(self, child):
    self.nbt_payload.append(child)
  def serialize_nbt(self):
    ret = pack('>B',self.nbt_id)
    if self.nbt_id != NBTID.End:
      ret += pack('>H',len(self.nbt_name))
      ret += self.nbt_name
      ret += self.serialize_payload()
    return ret
  def serialize_payload(self):
    if self.nbt_id == NBTID.End:
      pass
    elif self.nbt_id == NBTID.Byte:
      ret = pack('>B', self.nbt_payload)
    elif self.nbt_id == NBTID.Short:
      ret = pack('>h', self.nbt_payload)
    elif self.nbt_id == NBTID.Int:
      ret = pack('>i', self.nbt_payload)
    elif self.nbt_id == NBTID.Long:
      ret = pack('>q', self.nbt_payload)
    elif self.nbt_id == NBTID.Float:
      ret = pack('>f', self.nbt_payload)
    elif self.nbt_id == NBTID.Double:
      ret = pack('>d', self.nbt_payload)
    elif self.nbt_id == NBTID.Byte_Array:
      ret = pack('>i', len(self.nbt_payload))
      for elem in self.nbt_payload:
        try:
          ret += pack('>B', elem)
        except:
          print elem
          ret += pack('>B', int(elem))
    elif self.nbt_id == NBTID.String:
      ret = pack('>hs', len(self.nbt_payload), self.nbt_payload)
    elif self.nbt_id == NBTID.List:
      ret = pack('>Bi', self.nbt_payload[0].nbt_id, len(self.nbt_payload))
      for child in self.nbt_payload:
        ret += child.serialize_payload()
    elif self.nbt_id == NBTID.Compound:
      ret = "";
      for child in self.nbt_payload:
        ret += child.serialize_nbt()
      if self.nbt_payload[-1].nbt_id != NBTID.End:
        ret += NBT(NBTID.End).serialize_nbt()
    elif self.nbt_id == NBTID.Int_Array:
      ret = pack('>i', len(self.nbt_payload))
      for child in self.nbt_payload:
        ret += pack('>i', child.nbt_payload)
    return ret
  def __getitem__(self,childname):
    for child in self.nbt_payload:
      if child.nbt_name == childname:
        return child
    raise KeyError

def usage(status=-1):
  print "%s <xShift> <zShift> files [...] \n\n xShift and zShift are integers\n" % sys.argv[0]
  exit(status)

def main(xShift, zShift, files):
  xMin=None
  xMax=None
  zMin=None
  zMax=None
  # determine ranges
  for n in files:
    with gzip.open(n,"rb") as f:
      nbt = NBT.parse(f.read())
    scale = nbt["data"]["scale"].nbt_payload
    xCenter = nbt["data"]["xCenter"].nbt_payload
    zCenter = nbt["data"]["zCenter"].nbt_payload
    width = nbt["data"]["width"].nbt_payload
    height = nbt["data"]["height"].nbt_payload
    scalefactor = 2 ** scale
    left = xCenter - (width / 2) * scalefactor
    right = xCenter + (width / 2) * scalefactor -1
    top = zCenter - (height / 2) * scalefactor
    bottom = zCenter + (height / 2) * scalefactor -1
    xMin=left if xMin is None else min(xMin,left)
    xMax=right if xMax is None else max(xMax,right)
    zMin=top if zMin is None else min(zMin,top)
    zMax=bottom if zMax is None else max(zMax,bottom)
  # allocate array
  data = np.zeros((zMax+1-zMin,xMax+1-xMin), dtype=np.dtype('uint8'))
  print data.shape
  ## print data
  # read data (and modify)
  for n in files:
    with gzip.open(n,"rb") as f:
      nbt = NBT.parse(f.read())
    scale = nbt["data"]["scale"].nbt_payload
    xCenter = nbt["data"]["xCenter"].nbt_payload
    zCenter = nbt["data"]["zCenter"].nbt_payload
    width = nbt["data"]["width"].nbt_payload
    height = nbt["data"]["height"].nbt_payload
    scalefactor = 2 ** scale
    left = xCenter - (width / 2) * scalefactor
    right = xCenter + (width / 2) * scalefactor -1
    top = zCenter - (height / 2) * scalefactor
    bottom = zCenter + (height / 2) * scalefactor -1
    mapdata = np.asarray(nbt["data"]["colors"].nbt_payload)
    mapdata = mapdata.reshape((-1,width))
    mapdata = mapdata.repeat(scalefactor,axis=0).repeat(scalefactor,axis=1) 
    print xMin, zMin, left, right, top, bottom
    print "  ", left-xMin, right+1-xMin, top-zMin, bottom+1-zMin
    data[top-zMin:bottom+1-zMin,left-xMin:right+1-xMin] = mapdata
  # shift data
  newdata = np.roll(data,xShift,axis=1)
  newdata = np.roll(newdata,zShift,axis=0)
  # write data to png
  #im = Image.fromarray(newdata,mode='P')
  #im.putpalette(Palette)
  #im.save("/home/phineas/test.png")
  # write data back to files
  for n in files:
    with gzip.open(n,"rb") as f:
      nbt = NBT.parse(f.read())
    scale = nbt["data"]["scale"].nbt_payload
    xCenter = nbt["data"]["xCenter"].nbt_payload
    zCenter = nbt["data"]["zCenter"].nbt_payload
    width = nbt["data"]["width"].nbt_payload
    height = nbt["data"]["height"].nbt_payload
    scalefactor = 2 ** scale
    left = xCenter - (width / 2) * scalefactor
    right = xCenter + (width / 2) * scalefactor -1
    top = zCenter - (height / 2) * scalefactor
    bottom = zCenter + (height / 2) * scalefactor -1
    mapdata = newdata[top-zMin:bottom+1-zMin,left-xMin:right+1-xMin]
    mapdata = np.delete(mapdata,np.s_[::2],0)
    mapdata = np.delete(mapdata,np.s_[::2],1)
    colorPayload = mapdata.flatten().tolist()
    nbt["data"]["colors"].nbt_payload = colorPayload
    nbt["data"]["xCenter"].nbt_payload -= xShift
    nbt["data"]["zCenter"].nbt_payload -= zShift
    with gzip.open("/home/phineas/dump/%s"%n,"wb") as f:
      f.write(nbt.serialize_nbt())
    im = Image.fromarray(mapdata,mode='P')
    im.putpalette(Palette)
    im.save("/home/phineas/dump/%s.png"%n)
if __name__ == "__main__":
  integerPattern = re.compile('-?\d+')
  if len(sys.argv) <= 3:
    usage(1)
  if not re.match(integerPattern, sys.argv[1]):
    usage(2)
  if not re.match(integerPattern, sys.argv[2]):
    usage(3)
  try:
    xShift = int(sys.argv[1])
    zShift = int(sys.argv[2])
  except:
    usage(4)
  main(xShift, zShift, sys.argv[3:])
