#include "TH1.h"
#include "TF1.h"
#include "TROOT.h"
#include "TStyle.h"
#include "TMath.h"

double langaufun(double *x, double *par) {

   //Fit parameters:
   //par[0]=Width (scale) parameter of Landau density
   //par[1]=Most Probable (MP, location) parameter of Landau density
   //par[2]=Total area (integral -inf to inf, normalization constant)
   //par[3]=Width (sigma) of convoluted Gaussian function
   //
   //In the Landau distribution (represented by the CERNLIB approximation),
   //the maximum is located at x=-0.22278298 with the location parameter=0.
   //This shift is corrected within this function, so that the actual
   //maximum is identical to the MP parameter.

      // Numeric constants
      double invsq2pi = 0.3989422804014;   // (2 pi)^(-1/2)
      double mpshift  = -0.22278298;       // Landau maximum location

      // Control constants
      double np = 100.0;      // number of convolution steps
      double sc =   5.0;      // convolution extends to +-sc Gaussian sigmas

      // Variables
      double xx;
      double mpc;
      double fland;
      double sum = 0.0;
      double xlow,xupp;
      double step;
      double i;


      // MP shift correction
      mpc = par[1] - mpshift * par[0];

      // Range of convolution integral
      xlow = x[0] - sc * par[3];
      xupp = x[0] + sc * par[3];

      step = (xupp-xlow) / np;

      // Convolution integral of Landau and Gaussian by sum
      for(i=1.0; i<=np/2; i++) {
         xx = xlow + (i-.5) * step;
         fland = TMath::Landau(xx,mpc,par[0]) / par[0];
         sum += fland * TMath::Gaus(x[0],xx,par[3]);

         xx = xupp - (i-.5) * step;
         fland = TMath::Landau(xx,mpc,par[0]) / par[0];
         sum += fland * TMath::Gaus(x[0],xx,par[3]);
      }

      return (par[2] * step * sum * invsq2pi / par[3]);
}

TF1 *langaufit(TH1F *his, double *fitrange, double *startvalues, double *parlimitslo, double *parlimitshi, double *fitparams, double *fiterrors, double *ChiSqr, int *NDF)
{
   // Once again, here are the Landau * Gaussian parameters:
   //   par[0]=Width (scale) parameter of Landau density
   //   par[1]=Most Probable (MP, location) parameter of Landau density
   //   par[2]=Total area (integral -inf to inf, normalization constant)
   //   par[3]=Width (sigma) of convoluted Gaussian function
   //
   // Variables for langaufit call:
   //   his             histogram to fit
   //   fitrange[2]     lo and hi boundaries of fit range
   //   startvalues[4]  reasonable start values for the fit
   //   parlimitslo[4]  lower parameter limits
   //   parlimitshi[4]  upper parameter limits
   //   fitparams[4]    returns the final fit parameters
   //   fiterrors[4]    returns the final fit errors
   //   ChiSqr          returns the chi square
   //   NDF             returns ndf

   int i;
   char FunName[100];

   sprintf(FunName,"Fitfcn_%s",his->GetName());

   TF1 *ffitold = (TF1*)gROOT->GetListOfFunctions()->FindObject(FunName);
   if (ffitold) delete ffitold;

   TF1 *ffit = new TF1(FunName,langaufun,fitrange[0],fitrange[1],4);
   ffit->SetParameters(startvalues);
   ffit->SetParNames("Width","MP","Area","GSigma");

   for (i=0; i<4; i++) {
      ffit->SetParLimits(i, parlimitslo[i], parlimitshi[i]);
   }

   his->Fit(FunName,"RB0");   // fit within specified range, use ParLimits, do not plot

   ffit->GetParameters(fitparams);    // obtain fit parameters
   for (i=0; i<4; i++) {
      fiterrors[i] = ffit->GetParError(i);     // obtain fit parameter errors
   }
   ChiSqr[0] = ffit->GetChisquare();  // obtain chi^2
   NDF[0] = ffit->GetNDF();           // obtain ndf

   return (ffit);              // return fit function

}

/*
void langaus(){
  auto f = TFile::Open("langaus_hist.root");
  TH1F* hSNR = (TH1F*)( f->Get("clusterChargeAssociated")->Clone("hSNR"));
  double fr[2];
  double sv[4], pllo[4], plhi[4], fp[4], fpe[4];
  fr[0]=0.3*hSNR->GetMean();
  fr[1]=3.0*hSNR->GetMean();

  pllo[0]=10; pllo[1]=500.0; pllo[2]=1.0; pllo[3]=10.;
  plhi[0]=1000; plhi[1]=2000.0; plhi[2]=1000000.0; plhi[3]=1000.0;
  sv[0]=100; sv[1]=1000.0; sv[2]=10000.0; sv[3]=100.0;

  double chisqr;
  int    ndf;
  TF1 *fitsnr = langaufit(hSNR,fr,sv,pllo,plhi,fp,fpe,&chisqr,&ndf);
  hSNR->Draw();
  fitsnr->Draw("lsame");
}*/
