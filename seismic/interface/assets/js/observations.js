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
    $scope.showEvents = {};
    $scope.events = {};
    $scope.status = {};
    $scope.charts = {};
    $scope.detectSettings = {
        bandpassLow: 5,
        bandpassHigh: 10,
        shortWindow: 50,
        longWindow: 5000,
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
            url: 'observations/' + id
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
        $scope.charts[obs_id] = c3.generate({
            bindto: "#chart_" + obs_id,
            data: {
                url: "/observations/" + obs_id + "/view",
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
                            return date.toISOString();
                        },
                        count: 5,
                        culling: {
                           max: 5
                        }
                    }
                },
                y2: {
                    show: false,
                    default: [0, 10]
                }
            },
            grid: {
                y: {
                    lines: [{value: 0}]
                }
            },
            subchart: {show: true},
            point: {show: false}
        });
    };

    $scope.getEvents = function (obs_id) {
        $http({
            method: "GET",
            url: "/observations/" + obs_id + "/events"
        }).then(function (result) {
            $scope.events[obs_id] = result.data;
            result.data.forEach(function (x) {
                console.log("Marking from " + x.start);
                $scope.charts[obs_id].xgrids.add([
                    {value: x.start * 1000, text: 'Start', position: 'end'},
                    {value: x.end * 1000, text: 'End', position: 'end'}
                ]);
            });
            $scope.charts[obs_id].load({
                url: "/observations/" + obs_id + "/trigger_data",
                mimeType: "json",
                keys: {
                    x: 't',
                    value: ['lm', 'sm', 'trigger']
                },
                axes: {
                    lm: "y2",
                    sm: "y2",
                    trigger: "y2"
                }
            });
            $scope.charts[obs_id].show('axis.y2');
        })
    };

    $scope.getNetworks()
});
