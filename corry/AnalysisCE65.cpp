/**
 * @file
 * @brief Implementation of module AnalysisCE65
 *
 * @copyright Copyright (c) 2017-2022 CERN and the Corryvreckan authors.
 * This software is distributed under the terms of the MIT License, copied verbatim in the file "LICENSE.md".
 * In applying this license, CERN does not waive the privileges and immunities granted to it by virtue of its status as an
 * Intergovernmental Organization or submit itself to any jurisdiction.
 */

#include "AnalysisCE65.h"

#include "objects/Cluster.hpp"
#include "objects/Pixel.hpp"
#include "objects/Track.hpp"

#include <TDirectory.h>
#include <TFile.h>

using namespace corryvreckan;

AnalysisCE65::AnalysisCE65(Configuration& config, std::shared_ptr<Detector> detector)
    : AnalysisDUT(config, detector), m_detector(detector) {
    // Clustering
    windowSize_ = config_.get<int>("window_size", 3);

    // Read calibration file
    isCalibrated = false;
    hSensorPedestal = nullptr;
    hSensorNoise = nullptr;
    if(m_detector->getConfiguration().has("calibration_file")) {
        std::string tmp = m_detector->getConfiguration().getText("calibration_file"); // Return absolute path
        tmp = tmp.substr(1UL, tmp.size() - 2); // DEBUG: Remove double quotes around string
        auto f = new TFile(tmp.c_str(), "READ");
        if(f->IsOpen()) {
            LOG(INFO) << "Calibration file found - " << tmp;
            // Read histogram name from conf.
            std::string hTemp = config_.get<std::string>("calibration_pedestal");
            hSensorPedestal = dynamic_cast<TH2F*>(f->Get(hTemp.c_str())->Clone("sensorPedestal"));
            hTemp = config_.get<std::string>("calibration_noise");
            hSensorNoise = dynamic_cast<TH2F*>(f->Get(hTemp.c_str())->Clone("sensorNoise"));
            hSensorPedestal->SetDirectory(nullptr);
            hSensorNoise->SetDirectory(nullptr);
            f->Close();
            isCalibrated = true;
        } else {
            LOG(WARNING) << "Calibration file NOT FOUND - " << tmp;
        }
    }
}

void AnalysisCE65::initialize() {
    AnalysisDUT::initialize();

    // ClusteringAnalog
    TDirectory* directory = getROOTDirectory();
    TDirectory* local_directory = directory->mkdir("cluster");
    local_directory->cd();
    // Detector alignment/shift
    double dx = m_detector->displacement().x();
    double dy = m_detector->displacement().y();
    // Cluster plots
    std::string title;
    title = m_detector->getName() + " Cluster size;cluster size;events";
    clusterSize = new TH1F("clusterSize", title.c_str(), 100, -0.5, 99.5);
    title = m_detector->getName() + " Cluster charge;cluster charge (ADCu);events";
    clusterCharge = new TH1F("clusterCharge", title.c_str(), 2500, -4999.5, 20000.5);
    title = m_detector->getName() + " Cluster seed charge;cluster seed charge (ADCu);events";
    clusterSeedCharge = new TH1F("clusterSeedCharge", title.c_str(), 2100, -999.5, 20000.5);
    title = m_detector->getName() + " Cluster 3x3 charge;cluster 3x3 charge (ADCu);events";
    cluster3x3Charge = new TH1F("cluster3x3Charge", title.c_str(), 2100, -999.5, 20000.5);

    title = m_detector->getName() + " Cluster neighbours charge;Neighbours/pixel charge (ADCu);#clusters";
    clusterNeighboursCharge = new TH1F("clusterNeighboursCharge", title.c_str(), 2000, -9999.5, 10000.5);
    title = m_detector->getName() + " Sum of Cluster neighbours charge;Charge outside seed (ADCu);#pixels";
    clusterNeighboursChargeSum = new TH1F("clusterNeighboursChargeSum", title.c_str(), 2000, -9999.5, 10000.5);

    title = m_detector->getName() + " Cluster total charge ratio in N pixels;# pixel;charge ratio;events";
    clusterChargeRatio = new TH2F("clusterChargeRatio",
                                  title.c_str(),
                                  30,
                                  0.5,
                                  30.5, // N pixels
                                  130,
                                  -0.1,
                                  1.2); // charge ratio

    title = m_detector->getName() + " Cluster total charge ratio in N pixels;# pixel;charge ratio;events";
    clusterChargeHighestNpixels = new TH2F("clusterChargeHighestNpixels",
                                           title.c_str(),
                                           30,
                                           0.5,
                                           30.5, // N pixels
                                           2500,
                                           -4999.5,
                                           20000.5); // charge in highest N pixels

    title = m_detector->getName() + " Cluster seed S/N;S/N ratio;events";
    clusterSeedSNR = new TH1F("clusterSeedSNR", title.c_str(), 1000, -0.5, 99.5);
    title = m_detector->getName() + " Cluster neighbour S/N;S/N ratio;events";
    clusterNeighboursSNR = new TH1F("clusterNeighboursSNR", title.c_str(), 300, -10.5, 20.5);

    // Seeding - 2D correlation
    title = m_detector->getName() + " Seed charge vs neighbours;seed charge (ADCu);neighbours charge (ADCu);events";
    clusterSeed_Neighbours = new TH2F("clusterSeed_Neighbours", title.c_str(), 110, -999.5, 10000.5, 200, -9999.5, 10000.5);
    title = m_detector->getName() + " Seed SNR vs neighbours;seed S/N;neighbours S/N;events";
    clusterSeed_NeighboursSNR = new TH2F("clusterSeed_NeighboursSNR", title.c_str(), 1000, -0.5, 99.5, 300, -10.5, 20.5);
    title = m_detector->getName() + " Seed charge vs sum of neighbours;seed charge (ADCu);charge outside seed (ADCu);events";
    clusterSeed_NeighboursSum =
        new TH2F("clusterSeed_NeighboursSum", title.c_str(), 110, -999.5, 10000.5, 200, -9999.5, 10000.5);
    title = m_detector->getName() + " Seed charge vs cluster;seed charge (ADCu);cluster charge (ADCu);events";
    clusterSeed_Cluster = new TH2F("clusterSeed_Cluster", title.c_str(), 110, -999.5, 10000.5, 210, -999.5, 20000.5);
    title = m_detector->getName() + " Seed SNR vs cluster charge;seed S/N;cluster charge (ADCu);events";
    clusterSeedSNR_Cluster = new TH2F("clusterSeedSNR_Cluster", title.c_str(), 1000, -0.5, 99.5, 210, -999.5, 20000.5);

    // Cluster shape (charge distribution in window)
    title = m_detector->getName() + " Cluster charge distribution;pixel no.;pixel charge (ADCu);events";
    clusterChargeShape = new TH2F("clusterChargeShape", title.c_str(), 30, -14.5, 15.5, 200, -9999.5, 10000.5);
    title = m_detector->getName() + " Cluster charge distribution by S/N ratio;pixel no.;pixel S/N;events";
    clusterChargeShapeSNR = new TH2F("clusterChargeShapeSNR", title.c_str(), 30, -14.5, 15.5, 1100, -10.5, 99.5);
    title = m_detector->getName() + " Cluster charge distribution by ratio;pixel no.;pixel charge ratio;events";
    clusterChargeShapeRatio =
        new TH2F("clusterChargeShapeRatio", title.c_str(), 30, -14.5, 15.5, 240, -1.2, 1.2); // charge ratio

    // Cluster (central)
    title = m_detector->getName() + " Cluster size (central);cluster size;events";
    clusterSizeCentral = new TH1F("clusterSizeCentral", title.c_str(), 100, -0.5, 99.5);
    title = m_detector->getName() + " Cluster charge (central);cluster charge;events";
    clusterChargeCentral = new TH1F("clusterChargeCentral", title.c_str(), 1100, -99.5, 1000.5);
    title = m_detector->getName() + " Cluster seed charge (central);cluster seed charge;events";
    clusterSeedChargeCentral = new TH1F("clusterSeedChargeCentral", title.c_str(), 1100, -99.5, 1000.5);
    title = m_detector->getName() + " Cluster 3x3 charge (central);cluster 3x3 charge;events";
    cluster3x3ChargeCentral = new TH1F("cluster3x3ChargeCentral", title.c_str(), 1100, -99.5, 1000.5);

    title = m_detector->getName() + " Cluster position (global);x [mm];y [mm];events";
    clusterPositionGlobal = new TH2F("clusterPositionGlobal",
                                     title.c_str(),
                                     std::min(500, 5 * m_detector->nPixels().X()),
                                     -m_detector->getSize().X() / 1.5 + dx,
                                     m_detector->getSize().X() / 1.5 + dx,
                                     std::min(500, 5 * m_detector->nPixels().Y()),
                                     -m_detector->getSize().Y() / 1.5 + dy,
                                     m_detector->getSize().Y() / 1.5 + dy);
    title = m_detector->getName() + " Cluster position (local);x [px];y [px];events";
    clusterPositionLocal = new TH2F("clusterPositionLocal",
                                    title.c_str(),
                                    m_detector->nPixels().X(),
                                    -0.5,
                                    m_detector->nPixels().X() - 0.5,
                                    m_detector->nPixels().Y(),
                                    -0.5,
                                    m_detector->nPixels().Y() - 0.5);
    title = m_detector->getName() + " Cluster seed position (global);x [px];y [px];events";
    clusterSeedPositionGlobal = new TH2F("clusterSeedPositionGlobal",
                                         title.c_str(),
                                         std::min(500, 5 * m_detector->nPixels().X()),
                                         -m_detector->getSize().X() / 1.5 + dx,
                                         m_detector->getSize().X() / 1.5 + dx,
                                         std::min(500, 5 * m_detector->nPixels().Y()),
                                         -m_detector->getSize().Y() / 1.5 + dy,
                                         m_detector->getSize().Y() / 1.5 + dy);
    title = m_detector->getName() + " Cluster seed position (local);x [px];y [px];events";
    clusterSeedPositionLocal = new TH2F("clusterSeedPositionLocal",
                                        title.c_str(),
                                        m_detector->nPixels().X(),
                                        -0.5,
                                        m_detector->nPixels().X() - 0.5,
                                        m_detector->nPixels().Y(),
                                        -0.5,
                                        m_detector->nPixels().Y() - 0.5);
    directory->cd();
}

// Signal/Noise ratio
// return charge, ff calibration file is not available.
float AnalysisCE65::SNR(const Pixel* px) {
    if(!isCalibrated) {
        LOG(WARNING) << "Calibration file NOT initialized - return raw charge of (" << px->column() << "," << px->row()
                     << ")";
        return float(px->charge());
    }
    double pNoise = hSensorNoise->GetBinContent(px->column() + 1, px->row() + 1);
    if(pNoise > 0.)
        return float(px->charge() / pNoise);
    else {
        LOG(WARNING) << "Invalid noise value <" << pNoise << "> - return raw charge of (" << px->column() << "," << px->row()
                     << ")";
        return float(px->charge());
    }
}

// Fill analog clusters - charge, SNR, shape and correlations
void AnalysisCE65::fillClusterHistograms(const std::shared_ptr<Cluster>& cluster) {
    AnalysisDUT::fillClusterHistograms(cluster);

    auto seed = cluster->getSeedPixel();
    // Cluster info.
    clusterSize->Fill(static_cast<double>(cluster->size()));
    clusterCharge->Fill(cluster->charge());
    clusterSeedCharge->Fill(seed->charge());

    // Correlation
    clusterSeed_Cluster->Fill(seed->charge(), cluster->charge());
    clusterChargeShape->Fill(0., seed->charge());
    if(isCalibrated) {
        clusterSeedSNR->Fill(SNR(seed));
        clusterSeedSNR_Cluster->Fill(SNR(seed), cluster->charge());
        clusterChargeShapeSNR->Fill(0., SNR(seed));
    }

    double neighboursChargeSum = cluster->charge() - seed->charge();
    clusterNeighboursChargeSum->Fill(neighboursChargeSum);
    clusterSeed_NeighboursSum->Fill(seed->charge(), neighboursChargeSum);

    std::vector<double> chargeVals = {}; // pre-fill for sorting
    double chargeMax = 0.;
    for(auto px : cluster->pixels()) {
        double val = px->charge();
        if(isCalibrated) {
            clusterNeighboursSNR->Fill(SNR(px));
            clusterSeed_NeighboursSNR->Fill(SNR(seed), SNR(px));
        }
        clusterNeighboursCharge->Fill(val);
        clusterSeed_Neighbours->Fill(seed->charge(), val);
        chargeVals.push_back(val);
        if(val > 0)
            chargeMax += val;
    }

    // Fill cluster shape
    clusterChargeShapeRatio->Fill(0., seed->charge() / chargeMax);
    for(auto px : cluster->pixels()) {
        // Define index in seeding window
        int index = windowSize_ * (px->row() - seed->row()) + px->column() - seed->column();
        clusterChargeShape->Fill(index, px->charge());
        if(isCalibrated)
            clusterChargeShapeSNR->Fill(index, SNR(px));
        clusterChargeShapeRatio->Fill(index, px->charge() / chargeMax);
    }

    // Fill charge ratio by sorted charge
    double chargeRatio = 0.;
    double chargeHighestNpixels = 0.;
    int counter = 0;
    // sort neighbour pixels by charge (large first to count)
    std::sort(chargeVals.begin(), chargeVals.end(), std::greater<double>());
    for(auto val : chargeVals) {
        counter++;
        chargeHighestNpixels += val;
        chargeRatio += val / chargeMax;
        clusterChargeRatio->Fill(counter, chargeRatio);
        clusterChargeHighestNpixels->Fill(counter, chargeHighestNpixels);
    }

    // Central seeds
    if(seed->column() > 0 && seed->row() > 0 && seed->column() < m_detector->nPixels().Y() - 1 &&
       seed->row() < m_detector->nPixels().X() - 1) {
        clusterSizeCentral->Fill(static_cast<double>(cluster->size()));
        clusterChargeCentral->Fill(cluster->charge());
        clusterSeedChargeCentral->Fill(seed->charge());
    }

    // Fill position
    clusterPositionGlobal->Fill(cluster->global().x(), cluster->global().y());
    clusterPositionLocal->Fill(cluster->column(), cluster->row());

    auto seedLocal = m_detector->getLocalPosition(seed->column(), seed->row());
    auto seedGlobal = m_detector->localToGlobal(seedLocal);
    clusterSeedPositionGlobal->Fill(seedGlobal.x(), seedGlobal.y());
    clusterSeedPositionLocal->Fill(seed->column(), seed->row());
}

// Track Selection
// Cluster Selection

StatusCode AnalysisCE65::run(const std::shared_ptr<Clipboard>& clipboard) {
    return AnalysisDUT::run(clipboard);
}

void AnalysisCE65::finalize(const std::shared_ptr<ReadonlyClipboard>& clipboard) {
    AnalysisDUT::finalize(clipboard);
}