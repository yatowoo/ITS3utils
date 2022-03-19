#include "eudaq/StdEventConverter.hh"
#include "eudaq/RawEvent.hh"
#include <iostream>
#include <vector>
#include <cmath>

#include "TSystem.h"
#include "TFile.h"
#include "TH2.h"

class CE65RawEvent2StdEventConverter:public eudaq::StdEventConverter{
public:
  static const int X_MX_SIZE = 64;
  static const int Y_MX_SIZE = 32;
public:
  bool Converting(eudaq::EventSPC rawev,eudaq::StdEventSP stdev,eudaq::ConfigSPC conf) const override;
private:
  static TH2* hPedestal;
  static TH2* hNoise;
  void Dump(const std::vector<uint8_t> &data,size_t i) const;
};

// Definitions for static members
const int CE65RawEvent2StdEventConverter::X_MX_SIZE;
const int CE65RawEvent2StdEventConverter::Y_MX_SIZE;
TH2* CE65RawEvent2StdEventConverter::hPedestal = nullptr;
TH2* CE65RawEvent2StdEventConverter::hNoise = nullptr;

#define REGISTER_CONVERTER(name) namespace{auto dummy##name=eudaq::Factory<eudaq::StdEventConverter>::Register<CE65RawEvent2StdEventConverter>(eudaq::cstr2hash(#name));}
REGISTER_CONVERTER(CE65)
REGISTER_CONVERTER(CE65Raw)
REGISTER_CONVERTER(ce65_producer)


/** CE65Producer from https://gitlab.cern.ch/sbugiel/ce65_daq
Raw event name in data sender: CE65Raw
Raw event structure: decoded into pixel frames
Param: Corry configuration - key<calibration_file> (noise map from TAF)
**/
bool CE65RawEvent2StdEventConverter::Converting(eudaq::EventSPC in,eudaq::StdEventSP out,eudaq::ConfigSPC conf) const{
  // Read configuration file - cut mode
    // Case : StdEventMonitor
  bool flagSimpleCut = !conf;
    // Case : Corry analysis
  if(conf){ // TODO: pass conf from other case/usage
  std::string id = conf->Get("identifier",""); // set by corry
  if(id.find("CE65_") == std::string::npos) return false;  // Not sub-event for CE65
  std::string inputFileName = conf->Get("calibration_file","");
  if(inputFileName == "") inputFileName = "ce65.root"; // Try default file
  
  if(gSystem->AccessPathName(inputFileName.c_str())){
    flagSimpleCut = true;
  }else if(!hPedestal){ // Read only once for each run
    auto f = new TFile(inputFileName.c_str(), "READ");
    std::cout << "[+] CE65 - Input file : " << inputFileName.c_str() << std::endl;// DEBUG
    hPedestal = (TH2*)( f->Get("hPedestalpl1")->Clone("hPedestal"));
    hNoise = (TH2*)( f->Get("hnoisepl1")->Clone("hNoise"));
    hPedestal->SetDirectory(nullptr);
    hNoise->SetDirectory(nullptr);
    std::cout << "[+] CE65 - Noise map loaded."<< std::endl;// DEBUG
    f->Close();
  }}// End - Corry load conf.
  
  auto rawev=std::dynamic_pointer_cast<const eudaq::RawEvent>(in);
  // TODO: more than 1 plane(CE65)?, loop on rawev->GetEvecieN()
  eudaq::StandardPlane plane(rawev->GetDeviceN(),"ITS3DAQ","CE65");
  plane.SetSizeZS(X_MX_SIZE, Y_MX_SIZE,0,1);
  int iev = rawev->GetEventN();
  // ADC Cut without configuration
  const uint16_t N_SUBMATRIX = 3;
  uint16_t subEdge[N_SUBMATRIX] = {21, 42, 64}; // start from 0
  uint16_t subThr[N_SUBMATRIX] = {1500, 1800, 500}; // Avg. for sub-matrix 
  // Frame <-> Block (from Producer)
  std::vector<uint8_t> data=rawev->GetBlock(0); // 1st frame
  std::vector<uint8_t> dataLast = rawev->GetBlock(rawev->NumBlocks() - 1); // Last frame
  size_t n=data.size();
  for(int ix=0; ix < X_MX_SIZE; ix++){
    int thr = 0;
    for(int iSub = 0; iSub < N_SUBMATRIX; iSub++){
      if(ix < subEdge[iSub]){
        thr = subThr[iSub];
        break;
      }
    } 
    for(int iy=0; iy < Y_MX_SIZE; iy++){
      int iPixel = iy + ix * Y_MX_SIZE;
      uint8_t byteB = data[iPixel * sizeof(short) + 1];
      uint8_t byteA = data[iPixel * sizeof(short)];
      short valueFirst = short((byteB<<8)+byteA);
      byteB = dataLast[iPixel * sizeof(short) + 1];
      byteA = dataLast[iPixel * sizeof(short)];
      short valueLast = short((byteB<<8)+byteA);
      int value = std::abs(valueLast - valueFirst);
      if(!flagSimpleCut){
        float seedingSNR = 10.; // DEBUG - Read from conf
        float pNoise = hNoise->GetBinContent(ix+1, iy+1);
        if(pNoise > 0) plane.PushPixel(ix, iy, value / pNoise); // SNR as pulse
      }else if(value > thr){
        plane.PushPixel(ix, iy, 1);
      }
  }} // End - loop pixels
  
  out->AddPlane(plane);

  return true;
}

void CE65RawEvent2StdEventConverter::Dump(const std::vector<uint8_t> &data,size_t i) const {
  printf("[+] DEBUG : Dump event %d\n");
  for(int iy=0; iy < Y_MX_SIZE; iy++){
    printf("Y%2d\t",iy);
    for(int ix=0; ix < X_MX_SIZE; ix++){
      int iPixel = iy + ix * Y_MX_SIZE;
      uint8_t byteB = data[iPixel * sizeof(short) + 1];
      uint8_t byteA = data[iPixel * sizeof(short)];
      short valueFirst = short((byteB<<8)+byteA);
      printf("%d,", valueFirst);
    }
    printf("\b \n");
  }
}
