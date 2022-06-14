/**
 * @file
 * @brief Definition of module AnalysisCE65
 *
 * @copyright Copyright (c) 2017-2022 CERN and the Corryvreckan authors.
 * This software is distributed under the terms of the MIT License, copied verbatim in the file "LICENSE.md".
 * In applying this license, CERN does not waive the privileges and immunities granted to it by virtue of its status as an
 * Intergovernmental Organization or submit itself to any jurisdiction.
 */

#ifndef CORRYVRECKAN_ANALYSISCE65_H
#define CORRYVRECKAN_ANALYSISCE65_H

#include <TCanvas.h>
#include <TDirectory.h>
#include <TH1F.h>
#include <TH2F.h>
#include <TH3F.h>
#include <TProfile.h>
#include <TProfile2D.h>

#include <iostream>

#include "modules/AnalysisDUT/AnalysisDUT.h"
#include "modules/ClusteringAnalog/ClusteringAnalog.h"

namespace corryvreckan {
    /** @ingroup Modules
     */
    class AnalysisCE65 : public AnalysisDUT {
    public:
        // Constructors and destructors
        AnalysisCE65(Configuration& config, std::shared_ptr<Detector> detector);
        ~AnalysisCE65() {}

        // Functions
        void initialize() override;
        StatusCode run(const std::shared_ptr<Clipboard>& clipboard) override;
        void finalize(const std::shared_ptr<ReadonlyClipboard>& clipboard) override;

    protected:
        float SNR(const Pixel* px); // Signal/Noise ratio
        void fillClusterHistograms(const std::shared_ptr<Cluster>& cluster) override;

    private:
        // Cluster histograms
        TH1F* clusterSize;
        TH1F* clusterSeedCharge;
        TH1F* clusterCharge;
        TH1F* cluster3x3Charge;
        TH1F* clusterNeighboursCharge;
        TH1F* clusterNeighboursChargeSum;
        TH2F* clusterChargeRatio;
        TH2F* clusterChargeHighestNpixels;

        TH1F* clusterSeedSNR;
        TH1F* clusterNeighboursSNR;

        // Seeding - 2D correlation
        TH2F* clusterSeed_Neighbours;
        TH2F* clusterSeed_NeighboursSNR;
        TH2F* clusterSeed_NeighboursSum;
        TH2F* clusterSeed_Cluster;
        TH2F* clusterSeedSNR_Cluster;

        // Cluster shape (charge distribution)
        TH2F* clusterChargeShape;
        TH2F* clusterChargeShapeSNR;
        TH2F* clusterChargeShapeRatio;

        TH1F* clusterSizeCentral;
        TH1F* clusterSeedChargeCentral;
        TH1F* clusterChargeCentral;
        TH1F* cluster3x3ChargeCentral;

        TH2F* clusterPositionGlobal;
        TH2F* clusterPositionLocal;

        TH2F* clusterSeedPositionGlobal;
        TH2F* clusterSeedPositionLocal;

        // Calibration file
        TH2F* hSensorPedestal;
        TH2F* hSensorNoise;
        bool isCalibrated;

        int windowSize_;

        std::shared_ptr<Detector> m_detector;
    }; // Class AnalysisCE65
} // namespace corryvreckan

#endif // CORRYVRECKAN_ANALYSISCE65_H