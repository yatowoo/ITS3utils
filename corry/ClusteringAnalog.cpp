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

    require_detectors = config_.getArray<std::string>("require_detectors", {});

    rejectByROI = config_.get<bool>("reject_by_roi", false);
    windowSize = config_.get<int>("window_size", 3);
    thresholdSeed = config_.get<float>("threshold_seed");
    thresholdSeedSNR = config_.get<float>("thresholdSNR_seed", thresholdSeed);
    thresholdNeighbour = config_.get<float>("threshold_neighbour");
    thresholdNeighbourSNR = config_.get<float>("thresholdSNR_neighbour", thresholdNeighbour);

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
            // Read histogram name from conf.
            string hTemp = config_.get<string>("calibration_pedestal");
            hSensorPedestal = dynamic_cast<TH2F*>(f->Get(hTemp.c_str())->Clone("sensorPedestal"));
            hTemp = config_.get<string>("calibration_noise");
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

// Signal/Noise ratio
// return charge, ff calibration file is not available.
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

bool ClusteringAnalog::checkSeedCriteria(const std::shared_ptr<Pixel>& px) {
    if(isCalibrated)
        return (SNR(px) > thresholdSeedSNR);
    else
        return (px->charge() > thresholdSeed);
}

bool ClusteringAnalog::checkNeighbourCriteria(const std::shared_ptr<Pixel>& px) {
    if(isCalibrated)
        return (SNR(px) > thresholdNeighbourSNR);
    else
        return (px->charge() > thresholdNeighbour);
}

// Fill analog clusters - charge, SNR, shape and correlations
void ClusteringAnalog::fillHistograms(const std::shared_ptr<Cluster>& cluster,
                                      const std::shared_ptr<Pixel>& seed,
                                      const PixelVector& neighbours,
                                      double chargeTotal) {
    // Cluster info.
    clusterSize->Fill(static_cast<double>(cluster->size()));
    clusterCharge->Fill(cluster->charge());
    clusterSeedCharge->Fill(seed->charge());
    cluster3x3Charge->Fill(chargeTotal);

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

    std::vector<double> chargeVals = {seed->charge()}; // pre-fill for sorting
    double chargeMax = seed->charge();
    for(auto px : neighbours) {
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
    for(auto px : neighbours) {
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
    // sort neighbour pixels by charge (large first to count)
    std::sort(chargeVals.begin(), chargeVals.end(), greater<double>());
    for(auto val : chargeVals) {
        chargeRatio += val / chargeMax;
        clusterChargeRatio->Fill(++counter, chargeRatio);
    }

    // Central seeds
    if(seed->column() > 0 && seed->row() > 0 && seed->column() < m_detector->nPixels().Y() - 1 &&
       seed->row() < m_detector->nPixels().X() - 1) {
        clusterSizeCentral->Fill(static_cast<double>(cluster->size()));
        clusterChargeCentral->Fill(cluster->charge());
        clusterSeedChargeCentral->Fill(seed->charge());
        cluster3x3ChargeCentral->Fill(chargeTotal);
    }

    // Fill position
    clusterPositionGlobal->Fill(cluster->global().x(), cluster->global().y());
    clusterPositionLocal->Fill(cluster->column(), cluster->row());

    auto seedLocal = m_detector->getLocalPosition(seed->column(), seed->row());
    auto seedGlobal = m_detector->localToGlobal(seedLocal);
    clusterSeedPositionGlobal->Fill(seedGlobal.x(), seedGlobal.y());
    clusterSeedPositionLocal->Fill(seed->column(), seed->row());
}

// Event cut by ROI for quick check during testbeam
// Usage: in running conf, add ClusteringAnalog for DUT after all required references
bool ClusteringAnalog::checkEventCut(const std::shared_ptr<Clipboard>& clipboard) {
    // Find cluster in reference plane
    for(auto det : require_detectors) {
        auto clusters = clipboard->getData<Cluster>(det);
        if(clusters.empty()) {
            LOG(DEBUG) << "Cluster not found in <" << det << ">";
            return false;
        }
    }
    LOG(DEBUG) << "Event cuts PASS - start clustering on <" << m_detector->getName() << ">";
    return true;
}

StatusCode ClusteringAnalog::run(const std::shared_ptr<Clipboard>& clipboard) {

    if(!checkEventCut(clipboard))
        return StatusCode::Success;

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

    // Get the device dimensions
    int nRows = m_detector->nPixels().Y();
    int nCols = m_detector->nPixels().X();

    // Seeding
    PixelVector seedCandidates;
    for(auto pixel : pixels) {
        // Pre-fill the hitmap with pixels
        hitmap[pixel->column()][pixel->row()] = pixel;
        // Select seeds by threshold
        if(checkSeedCriteria(pixel)) {
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

        // TO DO: add timestamp

        // Search neighbours in a window around seed
        PixelVector neighbours;
        double chargeTotal = seed->charge();
        double xWeightTotal = double(seed->column()) * chargeTotal;
        double yWeightTotal = double(seed->row()) * chargeTotal;
        auto pxCenter = seed;
        int seedToEdge = (windowSize < 3) ? 1 : (windowSize - 1) / 2;
        for(int col = max(pxCenter->column() - seedToEdge, 0); col <= min(pxCenter->column() + seedToEdge, nCols - 1);
            col++) {
            for(int row = max(pxCenter->row() - seedToEdge, 0); row <= min(pxCenter->row() + seedToEdge, nRows - 1); row++) {
                auto pixel = hitmap[col][row];
                if(!pixel || used[pixel])
                    continue; // No pixel or already in other cluster

                if(checkNeighbourCriteria(pixel)) {
                    cluster->addPixel(&*pixel);
                    used[pixel] = true;
                    neighbours.push_back(pixel);
                } // Neighbours found over threshold

                // Sum FULL window around seed
                chargeTotal += pixel->charge();
                xWeightTotal += double(pixel->column()) * pixel->charge();
                yWeightTotal += double(pixel->row()) * pixel->charge();
            }
        } // Loop neighbours

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
        // Calculate global cluster position
        auto positionGlobal = m_detector->localToGlobal(positionLocal);

        cluster->setDetectorID(pixels.front()->detectorID());
        cluster->setClusterCentre(positionGlobal);
        cluster->setClusterCentreLocal(positionLocal);

        deviceClusters.push_back(cluster);

        LOG(DEBUG) << m_detector->getName() << " - cluster local: (" << cluster->column() << "," << cluster->row()
                   << ") - cluster global: " << cluster->global();

        // Output
        fillHistograms(cluster, seed, neighbours, chargeTotal);
        neighbours.clear();
    } // Loop - seedCandidates

    clipboard->putData(deviceClusters, m_detector->getName());
    LOG(DEBUG) << "Put " << deviceClusters.size() << " clusters on the clipboard for detector " << m_detector->getName()
               << ". From " << pixels.size() << " pixels";

    // Return value telling analysis to keep running
    return StatusCode::Success;
}

/*
 Function to calculate the centre of gravity of a cluster.
 Ignore pixels with 0 or negative charge
*/
void ClusteringAnalog::calculateClusterCentre(Cluster* cluster) {

    LOG(DEBUG) << "== Making cluster centre";
    // Empty variables to calculate cluster position
    double column(0), row(0), charge(0);
    double column_sum(0), column_sum_chargeweighted(0);
    double row_sum(0), row_sum_chargeweighted(0);

    // Get the pixels on this cluster
    auto pixels = cluster->pixels();
    string detectorID = pixels.front()->detectorID();
    LOG(DEBUG) << "- cluster has " << pixels.size() << " pixels";

    // Loop over all pixels
    for(auto& pixel : pixels) {
        // If charge <= 0 (use epsilon to avoid errors in floating-point arithmetic):
        if(pixel->charge() < std::numeric_limits<double>::epsilon()) {
            continue;
        }
        charge += pixel->charge();

        column_sum += pixel->column();
        row_sum += pixel->row();
        column_sum_chargeweighted += (pixel->column() * pixel->charge());
        row_sum_chargeweighted += (pixel->row() * pixel->charge());

        LOG(DEBUG) << "- pixel col, row: " << pixel->column() << "," << pixel->row();
    }

    assert(charge > 0);
    column = column_sum_chargeweighted / charge;
    row = row_sum_chargeweighted / charge;

    LOG(DEBUG) << "- cluster col, row: " << column << "," << row << " at time "
               << Units::display(cluster->timestamp(), "us");

    // Set the cluster parameters
    cluster->setRow(row);
    cluster->setColumn(column);
    cluster->setCharge(charge);
}