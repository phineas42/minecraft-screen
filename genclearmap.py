#!/usr/bin/python
import sys, re
from struct import *
# from enum import Enum
from collections import namedtuple
from pprint import *

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

class NBT:
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
      ret = pack('>b', self.nbt_payload)
    elif self.nbt_id == NBTID.Short:
      ret = pack('>h', self.nbt_payload)
    elif self.nbt_id == NBTID.Int:
      ret = pack('>i', self.nbt_payload)
    elif self.nbt_id == NBTID.Long:
      ret = pack('>l', self.nbt_payload)
    elif self.nbt_id == NBTID.Float:
      ret = pack('>f', self.nbt_payload)
    elif self.nbt_id == NBTID.Double:
      ret = pack('>d', self.nbt_payload)
    elif self.nbt_id == NBTID.Byte_Array:
      ret = pack('>i', len(self.nbt_payload))
      for elem in self.nbt_payload:
        try:
          ret += pack('>b', elem)
        except:
          ret += pack('>b', int(elem))
    elif self.nbt_id == NBTID.String:
      ret = pack('>hs', len(self.nbt_payload), self.nbt_payload)
    elif self.nbt_id == NBTID.List:
      ret = pack('>bi', self.nbt_payload[0].nbt_id, len(self.nbt_payload))
      for child in self.nbt_payload:
        ret += child.serialize_payload()
    elif self.nbt_id == NBTID.Compound:
      ret = "";
      for child in self.nbt_payload:
        ret += child.serialize_nbt()
      ret += NBT(NBTID.End).serialize_nbt()
    elif self.nbt_id == NBTID.Int_Array:
      ret = pack('>i', len(self.nbt_payload))
      for child in self.nbt_payload:
        ret += pack('>i', child.nbt_payload)
    return ret

def usage(status=-1):
  print "%s <xCenter> <zCenter>\n\n  xCenter and zCenter are integers\n" % sys.argv[0]
  exit(status)

def main(xCenter,zCenter):
  f=sys.stdout
  #print xCenter
  #print zCenter
  root = NBT(NBTID.Compound)
  data = NBT(NBTID.Compound, "data")
  data.append(NBT(NBTID.Byte, "scale", 1))
  data.append(NBT(NBTID.Byte, "dimension", 0))
  data.append(NBT(NBTID.Short, "height", 128))
  data.append(NBT(NBTID.Byte_Array, "colors", [0] * (128 * 128)))
  data.append(NBT(NBTID.Int, "xCenter", xCenter))
  data.append(NBT(NBTID.Short, "width", 128))
  data.append(NBT(NBTID.Int, "zCenter", zCenter))
  root.append(data)
  f.write(root.serialize_nbt())
  #print "Done"

if __name__ == "__main__":
  integerPattern = re.compile('-?\d+')
  if len(sys.argv) != 3:
    usage(1)
  if not re.match(integerPattern, sys.argv[1]):
    usage(2)
  if not re.match(integerPattern, sys.argv[2]):
    usage(3)
  try:
    xCenter = int(sys.argv[1])
    zCenter = int(sys.argv[2])
  except:
    usage(4)
  main(xCenter, zCenter)
