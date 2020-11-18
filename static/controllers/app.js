'use strict';

var app = angular.module('app',['ngRoute']);

function setRoutes($routeProvider,$locationProvider) {
    $routeProvider.when('/:id', {
        controller: 'main_ctrl',
        view: 'coap.html'
    });
}
app.config(['$routeProvider','$locationProvider',setRoutes]);

app.controller('main_ctrl', function($scope, $http, $timeout, $location, $routeParams) {

    $scope.state_proto = {
        email: null,
        numSequences: null,
        ready: false,
        processing: false,
        resultId: null,
        jsonAddress: null,
        virusVizAddress: null
    }

    $scope.state = Object.assign({}, $scope.state_proto);

    $scope.goWait = function(id){
        $location.path("/"+id); // path not hash
    }

    $scope.reset = function(){
        window.location.href="./";
    }

    $scope.UPLOAD_API = "api/upload/";
    $scope.POLL_API = "api/upload/status/";

    $scope.POLLING_TIMEOUT = 1000;

    $scope.MINUTES_PER_SEQ = 1;

    $scope.getCurrentLocation = function() {
        return $location.host();
    }

    $scope.poll = function(id) {

        console.log("Polling for ID: "+id);

        // Call the API
        $http({method: 'GET', url: $scope.POLL_API+id
        }).then(
            function success(response) {

                $scope.state.email = response.data.notifyTo;

                if( response.data.ready == true) {

                    $scope.state.jsonAddress = response.data.jsonAddress;
                    $scope.state.virusVizAddress = response.data.virusVizAddress;

                    $scope.state.processing = false;
                    $scope.state.ready = true;


                } else if(response.data.failed) {

                    $scope.state.processing = false;
                    $scope.state.ready = false;

                    bootbox.alert("Error: "+response.data.failedMessage);
                } else {
                    $timeout($scope.poll, $scope.POLLING_TIMEOUT, true, id);
                }



            },
            function error(response) {
                $scope.state.processing = false;
                $scope.state.ready = false;
                bootbox.alert("An error occurred. Response status: " + response.statusText+".");
            });

    }



    $scope.upload = function(requestBody) {

        $http({
            method: 'POST',
            data: $.param(requestBody),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            url: $scope.UPLOAD_API
        }).then(
            function success(response) {
                $scope.state.resultId = response.data.id;
                $scope.state.processing = true;

                $scope.goWait($scope.state.resultId);
            }
            ,
            function error(response) {
                bootbox.alert("An error occurred. Response status: " + response.statusText+".");
            }
        );

    }




    $scope.submit = function() {

        console.log("submit called");

        let fastaFile = document.getElementById('fasta');
        let metaFile = document.getElementById('meta');

        if (fastaFile.files.length === 0 || metaFile.files.length === 0)
            bootbox.alert("Please, select a FASTA file for sequences and a CSF file for metadata.");
        else {

            let fastaReader = new FileReader();

            fastaReader.onloadend = function (e_fasta) {

                console.log("FASTA was read.")

                let fastaText = e_fasta.target.result;
                let metaReader = new FileReader();

                metaReader.onloadend = function (e_meta) {

                    console.log("META was read.")

                    let metaText = e_meta.target.result;

                    $scope.state.numSequences = (fastaText.match(/>/g) || []).length;
                    // Add here check on CSV (metaText)

                    var message = "Your FASTA file contains " + $scope.state.numSequences + " sequence" +
                        ($scope.state.numSequences > 1 ? 's' : '') + ".<br>Do you want to proceed?";
                    bootbox.confirm(message, function (result) {

                        if (result) {

                            let requestBody = {
                                emailAddress: $scope.state.email,
                                fastaText: fastaText,
                                metaText: metaText
                            }

                            $scope.upload(requestBody);

                        }
                    });


                }
                metaReader.readAsText(metaFile.files[0]);
            }
            fastaReader.readAsText(fastaFile.files[0]);
        }
    }




    $scope.$on('$routeChangeSuccess', function() {

            if ("id" in $routeParams) {
                //console.log("found id "+$routeParams["id"]);
                $scope.state.resultId = $routeParams["id"];
                $scope.poll($scope.state.resultId);
            }
        }
    );




});


