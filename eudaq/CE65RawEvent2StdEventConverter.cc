#include "eudaq/StdEventConverter.hh"
#include "eudaq/RawEvent.hh"
#include <iostream>
#include <vector>
#include <cmath>

class CE65RawEvent2StdEventConverter:public eudaq::StdEventConverter{
public:
  static const int X_MX_SIZE = 64; 
  static const int Y_MX_SIZE = 32; 
public:
  bool Converting(eudaq::EventSPC rawev,eudaq::StdEventSP stdev,eudaq::ConfigSPC conf) const override;
};

// Definitions for stati members
const int CE65RawEvent2StdEventConverter::X_MX_SIZE;
const int CE65RawEvent2StdEventConverter::Y_MX_SIZE;

#define REGISTER_CONVERTER(name) namespace{auto dummy##name=eudaq::Factory<eudaq::StdEventConverter>::Register<CE65RawEvent2StdEventConverter>(eudaq::cstr2hash(#name));}
REGISTER_CONVERTER(CE65)

//
/** CE65Producer::RunLoop
  auto ev = eudaq::Event::MakeUnique("ce65Event");
  ev->SetTriggerN(trigger_n);
  ev->SetEventN(readyEvent.ev_number);
      
  for(uint iFrame =0; iFrame < readyEvent.frame.size(); iFrame++){
    std::vector<uint8_t> data;
    uint32_t block_id = iFrame;
    data.insert(data.end(), 
      &readyEvent.frame[iFrame].raw_amp[0][0],
      &readyEvent.frame[iFrame].raw_amp[0][0] + sizeof(readyEvent.frame[iFrame].raw_amp));
    ev->AddBlock(block_id, data);
  }
  SendEvent(std::move(ev));
**/
bool DPTSRawEvent2StdEventConverter::Converting(eudaq::EventSPC in,eudaq::StdEventSP out,eudaq::ConfigSPC conf) const{
  auto rawev=std::dynamic_pointer_cast<const eudaq::RawEvent>(in);
  // TODO: more than 1 plane(CE65)?, loop on rawev->GetEvecieN()
  eudaq::StandardPlane plane(rawev->GetDeviceN(),"ITS3DAQ","CE65");
  plane.SetSizeRaw(CE65RawEvent2StdEventConverter::Y_MX_SIZE, CE65RawEvent2StdEventConverter::X_MX_SIZE, rawev->NumBlocks())
  // Frame <-> Block (from Producer)
  for (int iFrame = 0; iFrame < rawev->NumBlocks(); iFrame++){
    std::vector<uint8_t> data=rawev->GetBlock(iFrame);
    size_t n=data.size();
    for(int ix=0; ix < CE65RawEvent2StdEventConverter::X_MX_SIZE; ix++){
      for(int iy=0; iy < CE65RawEvent2StdEventConverter::Y_MX_SIZE; iy++){
        int iPixel = iy + ix * CE65RawEvent2StdEventConverter::Y_MX_SIZE;
        plane.PushPixel(iy, ix, data.at(iPixel), (uint64_t)0, false, iFrame);
    }
  }// End - Frame/Block loop
  out->AddPlane(plane);

  return true;
}