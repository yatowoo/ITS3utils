/**
 * @file
 * @brief Implementation of module ClusteringAnalog
 *
 * @copyright Copyright (c) 2017-2021 CERN and the Corryvreckan authors.
 * This software is distributed under the terms of the MIT License, copied verbatim in the file "LICENSE.md".
 * In applying this license, CERN does not waive the privileges and immunities granted to it by virtue of its status as an
 * Intergovernmental Organization or submit itself to any jurisdiction.
 */

#include "ClusteringAnalog.h"
#include "objects/Pixel.hpp"

#include <TFile.h>

using namespace corryvreckan;
using namespace std;

ClusteringAnalog::ClusteringAnalog(Configuration& config, std::shared_ptr<Detector> detector)
    : Module(config, detector), m_detector(detector) {

    rejectByROI = config_.get<bool>("reject_by_roi", false);
    windowSize = config_.get<int>("window_size", 3);
    thresholdSeed = config_.get<float>("threshold_seed");
    thresholdSeedSNR = config_.get<float>("thresholdSNR_seed", thresholdSeed);
    thresholdNeighbour = config_.get<float>("threshold_neighbour");
    thresholdNeighbourSNR = config_.get<float>("thresholdSNR_neighbour", thresholdNeighbour);
    // Digital option - by detector type
    digital_detectors_ = config_.getArray<std::string>("digital_detectors", {});
    isDigital = false;

    string tmp = config_.get<string>("method", "cluster");
    if(tmp == "seed")
        coordinates = EstimationMethod::seed;
    else if(tmp == "cluster")
        coordinates = EstimationMethod::cluster;
    else if(tmp == "sum3x3")
        coordinates = EstimationMethod::sum3x3;
    else {
        LOG(ERROR) << "Coordinates \"" << tmp << "\" not understood -- using \"cluster\" instead.";
        coordinates = EstimationMethod::cluster;
    }

    tmp = config_.get<string>("seeding_method", "multi");
    if(tmp == "max")
        seedingType = SeedingMethod::max;
    else if(tmp == "multi")
        seedingType = SeedingMethod::multi;
    else {
        LOG(ERROR) << "Seeding method <" << tmp << "> not defined -- using <multi> instead";
        seedingType = SeedingMethod::multi;
    }

    // Read calibration file
    isCalibrated = false;
    hSensorPedestal = nullptr;
    hSensorNoise = nullptr;
    if(m_detector->getConfiguration().has("calibration_file")) {
        tmp = m_detector->getConfiguration().getText("calibration_file"); // Return absolute path
        tmp = tmp.substr(1UL, tmp.size() - 2);                            // DEBUG: Remove double quotes around string
        auto f = new TFile(tmp.c_str(), "READ");
        if(f->IsOpen()) {
            LOG(INFO) << "Calibration file found - " << tmp;
            // DEBUG: CE65 generated from TAF, TODO: set hName in conf.
            hSensorPedestal = dynamic_cast<TH2F*>(f->Get("hPedestalpl1")->Clone("sensorPedestal"));
            hSensorNoise = dynamic_cast<TH2F*>(f->Get("hnoisepl1")->Clone("sensorNoise"));
            hSensorPedestal->SetDirectory(nullptr);
            hSensorNoise->SetDirectory(nullptr);
            f->Close();
            isCalibrated = true;
        } else {
            LOG(WARNING) << "Calibration file NOT FOUND - " << tmp;
        }
    }

    resetDigital();
}

void ClusteringAnalog::resetDigital() {
    isDigital = false;

    for(auto dType : digital_detectors_) {
        if(!strcasecmp(m_detector->getType().c_str(), dType.c_str())) {
            isDigital = true;
            // For ALPIDE, pixel amp. value is 1
            thresholdSeed = 0.5;
            thresholdSeedSNR = 0.5; // unused
            thresholdNeighbour = 0.5;
            thresholdNeighbourSNR = 0.5; // unused
            coordinates = EstimationMethod::cluster;
            seedingType = SeedingMethod::multi;
            isCalibrated = false;
            break;
        }
    }
}

void ClusteringAnalog::initialize() {
    // TO OD: make ranges configurable
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

    title = m_detector->getName() + " Cluster neighbors charge;Neighbors/pixel charge (ADCu);#clusters";
    clusterNeighborsCharge = new TH1F("clusterNeighborsCharge", title.c_str(), 2000, -9999.5, 10000.5);
    title = m_detector->getName() + " Sum of Cluster neighbors charge;Charge outside seed (ADCu);#pixels";
    clusterNeighborsChargeSum = new TH1F("clusterNeighborsChargeSum", title.c_str(), 2000, -9999.5, 10000.5);

    title = m_detector->getName() + " Cluster total charge ratio in N pixels;# pixel;charge ratio;events";
    clusterChargeRatio = new TH2F("clusterChargeRatio",
                                  title.c_str(),
                                  30,
                                  0.5,
                                  30.5, // N pixels
                                  130,
                                  -0.1,
                                  1.2); // charge ratio

    title = m_detector->getName() + " Cluster seed S/N;S/N ratio;events";
    clusterSeedSNR = new TH1F("clusterSeedSNR", title.c_str(), 1000, -0.5, 99.5);
    title = m_detector->getName() + " Cluster neighbor S/N;S/N ratio;events";
    clusterNeighborsSNR = new TH1F("clusterNeighborsSNR", title.c_str(), 300, -10.5, 20.5);

    // Seeding - 2D correlation
    title = m_detector->getName() + " Seed charge vs neighbors;seed charge (ADCu);neighbors charge (ADCu);events";
    clusterSeed_Neighbors = new TH2F("clusterSeed_Neighbors", title.c_str(), 110, -999.5, 10000.5, 200, -9999.5, 10000.5);
    title = m_detector->getName() + " Seed SNR vs neighbors;seed S/N;neighbors S/N;events";
    clusterSeed_NeighborsSNR = new TH2F("clusterSeed_NeighborsSNR", title.c_str(), 1000, -0.5, 99.5, 300, -10.5, 20.5);
    title = m_detector->getName() + " Seed charge vs sum of neighbors;seed charge (ADCu);charge outside seed (ADCu);events";
    clusterSeed_NeighborsSum =
        new TH2F("clusterSeed_NeighborsSum", title.c_str(), 110, -999.5, 10000.5, 200, -9999.5, 10000.5);
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
    title = m_detector->getName() + " Cluster seed charge (cetral);cluster seed charge;events";
    clusterSeedChargeCentral = new TH1F("clusterSeedChargeCentral", title.c_str(), 1100, -99.5, 1000.5);
    title = m_detector->getName() + " Cluster 3x3 charge (central);cluster 3x3 charge;events";
    cluster3x3ChargeCentral = new TH1F("cluster3x3ChargeCentral", title.c_str(), 1100, -99.5, 1000.5);

    title = m_detector->getName() + " Cluster position (global);x [mm];y [mm];events";
    clusterPositionGlobal = new TH2F("clusterPositionGlobal",
                                     title.c_str(),
                                     min(500, 5 * m_detector->nPixels().X()),
                                     -m_detector->getSize().X() / 1.5 + dx,
                                     m_detector->getSize().X() / 1.5 + dx,
                                     min(500, 5 * m_detector->nPixels().Y()),
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
                                         min(500, 5 * m_detector->nPixels().X()),
                                         -m_detector->getSize().X() / 1.5 + dx,
                                         m_detector->getSize().X() / 1.5 + dx,
                                         min(500, 5 * m_detector->nPixels().Y()),
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
}

float ClusteringAnalog::SNR(const std::shared_ptr<Pixel>& px) {
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

bool ClusteringAnalog::findSeed(const std::shared_ptr<Pixel>& px) {
    if(isCalibrated)
        return (SNR(px) > thresholdSeedSNR);
    else
        return (px->charge() > thresholdSeed);
}

bool ClusteringAnalog::findNeighbor(const std::shared_ptr<Pixel>& px) {
    if(isCalibrated)
        return (SNR(px) > thresholdNeighbourSNR);
    else
        return (px->charge() > thresholdSeedSNR);
}

// Fill analog clusters - SNR,
void ClusteringAnalog::fillAnalog(const std::shared_ptr<Cluster>& cluster,
                                  const std::shared_ptr<Pixel>& seed,
                                  const PixelVector& neighbors) {
    clusterSeed_Cluster->Fill(seed->charge(), cluster->charge());
    clusterChargeShape->Fill(0., seed->charge());
    if(isCalibrated) {
        clusterSeedSNR->Fill(SNR(seed));
        clusterSeedSNR_Cluster->Fill(SNR(seed), cluster->charge());
        clusterChargeShapeSNR->Fill(0., SNR(seed));
    }

    double neighborsChargeSum = cluster->charge() - seed->charge();
    clusterNeighborsChargeSum->Fill(neighborsChargeSum);
    clusterSeed_NeighborsSum->Fill(seed->charge(), neighborsChargeSum);

    std::vector<double> chargeVals = {seed->charge()}; // pre-fill for sorting
    double chargeMax = seed->charge();
    for(auto px : neighbors) {
        double val = px->charge();
        if(isCalibrated) {
            clusterNeighborsSNR->Fill(SNR(px));
            clusterSeed_NeighborsSNR->Fill(SNR(seed), SNR(px));
        }
        clusterNeighborsCharge->Fill(val);
        clusterSeed_Neighbors->Fill(seed->charge(), val);
        chargeVals.push_back(val);
        if(val > 0)
            chargeMax += val;
    }

    // Fill cluster shape
    clusterChargeShapeRatio->Fill(0., seed->charge() / chargeMax);
    for(auto px : neighbors) {
        // Define index in seeding window
        int index = windowSize * (px->row() - seed->row()) + px->column() - seed->column();
        clusterChargeShape->Fill(index, px->charge());
        if(isCalibrated)
            clusterChargeShapeSNR->Fill(index, SNR(px));
        clusterChargeShapeRatio->Fill(index, px->charge() / chargeMax);
    }

    // Fill charge ratio by sorted charge
    double chargeRatio = 0.;
    int counter = 0;
    // sort neighbor pixels by charge (large first to count)
    std::sort(chargeVals.begin(), chargeVals.end(), greater<double>());
    for(auto val : chargeVals) {
        chargeRatio += val / chargeMax;
        clusterChargeRatio->Fill(++counter, chargeRatio);
    }
}

StatusCode ClusteringAnalog::run(const std::shared_ptr<Clipboard>& clipboard) {

    // Get the pixels
    auto pixels = clipboard->getData<Pixel>(m_detector->getName());
    if(pixels.empty()) {
        LOG(DEBUG) << "Detector " << m_detector->getName() << " does not have any pixels on the clipboard";
        return StatusCode::Success;
    }

    // Make the cluster container and the maps for clustering
    ClusterVector deviceClusters;
    map<std::shared_ptr<Pixel>, bool> used;
    map<int, map<int, std::shared_ptr<Pixel>>> hitmap;
    bool addedPixel;

    // Get the device dimensions
    int nRows = m_detector->nPixels().Y();
    int nCols = m_detector->nPixels().X();

    // Seeding
    PixelVector seedCandidates;
    for(auto pixel : pixels) {
        // Pre-fill the hitmap with pixels
        hitmap[pixel->column()][pixel->row()] = pixel;
        // Select seeds by threshold
        if(findSeed(pixel)) {
            switch(seedingType) {
            case SeedingMethod::max:
                if(seedCandidates.empty() || pixel->charge() > seedCandidates[0]->charge()) {
                    seedCandidates.clear();
                    seedCandidates.push_back(pixel);
                }
                break;
            case SeedingMethod::multi:
            default:
                seedCandidates.push_back(pixel);
                break;
            }
        }
    } // Loop pixels pre-clustering

    // Reconstruct clusters from seeds
    for(auto seed : seedCandidates) {
        if(used[seed])
            continue;

        // New seed/pixel => new cluster
        auto cluster = std::make_shared<Cluster>();
        cluster->addPixel(&*seed);
        used[seed] = true;

        // TODO: add timestamp

        // Search neighbors
        PixelVector neighbors;
        double chargeTotal = seed->charge();
        double xWeightTotal = double(seed->column()) * chargeTotal;
        double yWeightTotal = double(seed->row()) * chargeTotal;
        addedPixel = true;
        auto pxCenter = seed;
        while(addedPixel) { // flag used for touching method
            addedPixel = false;

            int seedToEdge = isDigital ? 1 : (windowSize - 1) / 2;
            for(int col = max(pxCenter->column() - seedToEdge, 0); col <= min(pxCenter->column() + seedToEdge, nCols - 1);
                col++) {
                for(int row = max(pxCenter->row() - seedToEdge, 0); row <= min(pxCenter->row() + seedToEdge, nRows - 1);
                    row++) {
                    auto pixel = hitmap[col][row];
                    if(!pixel || used[pixel])
                        continue; // No pixel or already in other cluster

                    if(findNeighbor(pixel)) {
                        cluster->addPixel(&*pixel);
                        used[pixel] = true;
                        neighbors.push_back(pixel);
                    } // Neighbors found over threshold

                    if(isDigital)
                        continue;
                    // Sum FULL window around seed
                    chargeTotal += pixel->charge();
                    xWeightTotal += double(pixel->column()) * pixel->charge();
                    yWeightTotal += double(pixel->row()) * pixel->charge();
                }
            } // Loop neighbors

            // Touching-neighbors method (only for digital now)
            if(isDigital && neighbors.size() > 0) {
                addedPixel = true;
                pxCenter = neighbors.back();
                neighbors.pop_back();
            } else
                break; // make sure to end loop
        }              // Loop - connecting all neighbors

        // Finalise the cluster and save it
        switch(coordinates) {
        case EstimationMethod::seed:
            cluster->setRow(seed->row());
            cluster->setColumn(seed->column());
            cluster->setCharge(seed->charge());
            break;
        case EstimationMethod::sum3x3:
            if(chargeTotal > 0) {
                cluster->setRow(yWeightTotal / chargeTotal);
                cluster->setColumn(xWeightTotal / chargeTotal);
            } else {
                LOG(WARNING) << "Zero charge found in clustering (sum3x3 method)" << endl;
                cluster->setRow(seed->row());
                cluster->setColumn(seed->column());
            }
            cluster->setCharge(chargeTotal);
            break;
        case EstimationMethod::cluster:
        default:
            calculateClusterCentre(cluster.get());
            break;
        }

        // check if the cluster is within ROI
        if(rejectByROI && !m_detector->isWithinROI(cluster.get())) {
            LOG(DEBUG) << "Rejecting cluster outside of " << m_detector->getName() << " ROI";
            continue;
        }

        // Set uncertainty on position from intrinstic detector spatial resolution:
        cluster->setError(m_detector->getSpatialResolution());

        // Create object with local cluster position
        auto positionLocal = m_detector->getLocalPosition(cluster->column(), cluster->row());
        auto seedLocal = m_detector->getLocalPosition(seed->column(), seed->row());

        // Calculate global cluster position
        auto positionGlobal = m_detector->localToGlobal(positionLocal);
        auto seedGlobal = m_detector->localToGlobal(seedLocal);

        cluster->setDetectorID(pixels.front()->detectorID());
        cluster->setClusterCentre(positionGlobal);
        cluster->setClusterCentreLocal(positionLocal);

        deviceClusters.push_back(cluster);

        LOG(DEBUG) << m_detector->getName() << " - cluster local: (" << cluster->column() << "," << cluster->row()
                   << ") - cluster global: " << cluster->global();

        // Output - fill histograms
        clusterSize->Fill(static_cast<double>(cluster->size()));
        clusterCharge->Fill(cluster->charge());
        clusterSeedCharge->Fill(seed->charge());
        cluster3x3Charge->Fill(chargeTotal);

        if(!isDigital)
            fillAnalog(cluster, seed, neighbors);
        neighbors.clear();

        // ROI?
        if(seed->column() > 0 && seed->row() > 0 && seed->column() < nRows - 1 && seed->row() < nCols - 1) {
            clusterSizeCentral->Fill(static_cast<double>(cluster->size()));
            clusterChargeCentral->Fill(cluster->charge());
            clusterSeedChargeCentral->Fill(seed->charge());
            cluster3x3ChargeCentral->Fill(chargeTotal);
        }

        clusterPositionGlobal->Fill(cluster->global().x(), cluster->global().y());
        clusterPositionLocal->Fill(cluster->column(), cluster->row());

        clusterSeedPositionGlobal->Fill(seedGlobal.x(), seedGlobal.y());
        clusterSeedPositionLocal->Fill(seed->column(), seed->row());
    } // Loop - seedCandidates

    clipboard->putData(deviceClusters, m_detector->getName());
    LOG(DEBUG) << "Put " << deviceClusters.size() << " clusters on the clipboard for detector " << m_detector->getName()
               << ". From " << pixels.size() << " pixels";

    // Return value telling analysis to keep running
    return StatusCode::Success;
}

/*
 Function to calculate the centre of gravity of a cluster.
 Sets the local and global cluster positions as well.
*/
void ClusteringAnalog::calculateClusterCentre(Cluster* cluster) {
    bool chargeWeighting = true;

    LOG(DEBUG) << "== Making cluster centre";
    // Empty variables to calculate cluster position
    double column(0), row(0), charge(0);
    double column_sum(0), column_sum_chargeweighted(0);
    double row_sum(0), row_sum_chargeweighted(0);
    bool found_charge_zero = false;

    // Get the pixels on this cluster
    auto pixels = cluster->pixels();
    string detectorID = pixels.front()->detectorID();
    LOG(DEBUG) << "- cluster has " << pixels.size() << " pixels";

    // Loop over all pixels
    for(auto& pixel : pixels) {
        // If charge == 0 (use epsilon to avoid errors in floating-point arithmetic):
        if(pixel->charge() < std::numeric_limits<double>::epsilon()) {
            // apply arithmetic mean if a pixel has zero charge
            found_charge_zero = true;
        }
        charge += pixel->charge();

        // We need both column_sum and column_sum_chargeweighted
        // as we don't know a priori if there will be a pixel with
        // charge==0 such that we have to fall back to the arithmetic mean.
        column_sum += pixel->column();
        row_sum += pixel->row();
        column_sum_chargeweighted += (pixel->column() * pixel->charge());
        row_sum_chargeweighted += (pixel->row() * pixel->charge());

        LOG(DEBUG) << "- pixel col, row: " << pixel->column() << "," << pixel->row();
    }

    if(chargeWeighting && !found_charge_zero) {
        // Charge-weighted centre-of-gravity for cluster centre:
        // (here it's safe to divide by the charge as it cannot be zero due to !found_charge_zero)
        column = column_sum_chargeweighted / charge;
        row = row_sum_chargeweighted / charge;
    } else {
        // Arithmetic cluster centre:
        column = column_sum / static_cast<double>(cluster->size());
        row = row_sum / static_cast<double>(cluster->size());
    }

    LOG(DEBUG) << "- cluster col, row: " << column << "," << row << " at time "
               << Units::display(cluster->timestamp(), "us");

    // Set the cluster parameters
    cluster->setRow(row);
    cluster->setColumn(column);
    cluster->setCharge(charge);
}