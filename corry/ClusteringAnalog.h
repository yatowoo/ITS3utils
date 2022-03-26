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
        // Reset configuration for digital detectors
        void resetDigital();

        void calculateClusterCentre(Cluster*);

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

        TH1F* clusterSizeCentral;
        TH1F* clusterSeedChargeCentral;
        TH1F* clusterChargeCentral;
        TH1F* cluster3x3ChargeCentral;

        TH2F* clusterPositionGlobal;
        TH2F* clusterPositionLocal;

        TH2F* clusterSeedPositionGlobal;
        TH2F* clusterSeedPositionLocal;

        float thresholdSeed;
        float thresholdNeighbour;
        std::vector<std::string> digital_detectors_;

        bool isDigital;
    };
} // namespace corryvreckan
#endif // ClusteringAnalog_H
