var app = angular.module('obs', []);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

app.controller('obsCtrl', function($scope, $http) {
    $scope.selectedNetwork = null;
    $scope.selectedChannel = null;
    $scope.selectedStation = null;
    $scope.networks = [];
    $scope.stations = [];
    $scope.channels = [];
    $scope.observations = [];
    $scope.showOptions = {};
    $scope.status = {};
    $scope.charts = [];
    $scope.detectSettings = {
        bandpassLow: 5,
        bandpassHigh: 10,
        shortWindow: 250,
        longWindow: 15000,
        nStds: 3,
        triggerLen: 5000
    };

    $scope.getNetworks = function() {
        $http({
            method: 'GET',
            url: '/observations/search'
        }).then(function (result) {
            $scope.networks = result.data;
        });
    };

    $scope.getStations = function() {
        $http({
            method: 'GET',
            url: '/observations/search',
            params: {
                network: $scope.selectedNetwork
            }
        }).then(function(result) {
            $scope.stations = result.data;
        })
    };

    $scope.getChannels = function() {
        $http({
            method: 'GET',
            url: '/observations/search',
            params: {
                network: $scope.selectedNetwork,
                station: $scope.selectedStation
            }
        }).then(function(result) {
            $scope.channels = result.data;
        })
    };

    $scope.getObservations = function() {
        $http({
            method: 'GET',
            url: '/observations/search',
            params: {
                network: $scope.selectedNetwork,
                station: $scope.selectedStation,
                channel: $scope.selectedChannel
            }
        }).then(function(result) {
            $scope.observations = result.data;
            $scope.observations.forEach(function (o) {
                $scope.status[o.id] = "Potential Events: " + o.events;
            })
        })
    };

    $scope.deleteObservation = function(id) {
        console.log("Got DELETE:" + id);
        $http({
            method: 'DELETE',
            url: 'observatiPotential Events: {a i.events a}ons/' + id
        }).then(function() {
            $scope.getObservations()
        })
    };

    $scope.deleteEvents = function(id) {
        console.log("Got DELETE Events:" + id);
        $http({
            method: 'DELETE',
            url: 'observations/' + id,
            params: { eventsOnly: true}
        }).then(function() {
            $scope.getObservations()
        })
    };

    $scope.detectEvents = function (id) {
        // This does not copy
        var p = $scope.detectSettings;
        p.obsId = id;
        $http({
            method: 'GET',
            url: '/run/detect',
            params: p
        }).then(function(result) {
            $scope.status[id] = "Dispatched job: " + result.data.taskId;
            console.log("Dispatched job " + result.data.taskId + " for obs: " + id)
        });
    };

    $scope.renderChart = function (obs_id) {
        console.log("Rendering " + obs_id)
        return c3.generate({
            bindto: "#chart_" + obs_id,
            data: {
                url: "/observations/view/" + obs_id,
                mimeType: "json",
                keys: {
                    x: 't',
                    value: ['y']
                }
            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        format: function (e) {
                            var date = new Date(e);
                            return date.toTimeString();
                        }
                    }
                }
            },
            subchart: {show: true},
            point: {show: false}
        });
    };

    $scope.getNetworks()
});
