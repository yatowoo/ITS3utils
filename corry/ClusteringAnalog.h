/**
 * @file
 * @brief Definition of module ClusteringAnalog
 *
 * @copyright Copyright (c) 2017-2021 CERN and the Corryvreckan authors.
 * This software is distributed under the terms of the MIT License, copied verbatim in the file "LICENSE.md".
 * In applying this license, CERN does not waive the privileges and immunities granted to it by virtue of its status as an
 * Intergovernmental Organization or submit itself to any jurisdiction.
 */

#ifndef ClusteringAnalog_H
#define ClusteringAnalog_H 1

#include <TCanvas.h>
#include <TH1F.h>
#include <TH2F.h>
#include <iostream>
#include "core/module/Module.hpp"
#include "objects/Cluster.hpp"

namespace corryvreckan {
    /** @ingroup Modules
     */
    class ClusteringAnalog : public Module {

    public:
        // Constructors and destructors
        ClusteringAnalog(Configuration& config, std::shared_ptr<Detector> detector);
        ~ClusteringAnalog() {}

        // Functions
        void initialize() override;
        StatusCode run(const std::shared_ptr<Clipboard>& clipboard) override;

    private:
        void calculateClusterCentre(Cluster*);

        float SNR(const std::shared_ptr<Pixel>& px); // Signal/Noise ratio
        bool checkSeedCriteria(const std::shared_ptr<Pixel>& px);
        bool checkNeighbourCriteria(const std::shared_ptr<Pixel>& px);
        bool checkEventCut(const std::shared_ptr<Clipboard>& clipboard);
        void fillHistograms(const std::shared_ptr<Cluster>& cluster,
                            const std::shared_ptr<Pixel>& seed,
                            const PixelVector& neighbours,
                            double chargeTotal);

    private:
        enum class EstimationMethod {
            seed,
            cluster,
            sum3x3,
        } coordinates;

        enum class SeedingMethod {
            max,
            multi,
        } seedingType;

        std::shared_ptr<Detector> m_detector;

        // Cluster histograms
        TH1F* clusterSize;
        TH1F* clusterSeedCharge;
        TH1F* clusterCharge;
        TH1F* cluster3x3Charge;
        TH1F* clusterNeighboursCharge;
        TH1F* clusterNeighboursChargeSum;
        TH2F* clusterChargeRatio;

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

        bool rejectByROI;
        std::vector<std::string> require_detectors; // Event cut
        // Threshold - raw value (ADC unit, TOT, ...)
        float thresholdSeed;
        float thresholdNeighbour;

        int windowSize; // Cluster matrix to search neighbours

        // Threshold - Signal/Noise ratio (require calibration)
        float thresholdSeedSNR;
        float thresholdNeighbourSNR;
        // Calibration file
        TH2F* hSensorPedestal;
        TH2F* hSensorNoise;
        bool isCalibrated;
    };
} // namespace corryvreckan
#endif // ClusteringAnalog_H
