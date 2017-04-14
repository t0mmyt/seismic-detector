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
        })
    };

    $scope.getNetworks()
});