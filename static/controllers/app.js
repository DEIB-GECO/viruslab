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
    $scope.VCF_API = "api/vcf-download/";
    $scope.POLL_API = "api/upload/status/";
    $scope.POLL_VCF_API = "api/vcf-download/status/";


    $scope.POLLING_TIMEOUT = 3000;

    $scope.MINUTES_PER_SEQ = 2;

    $scope.getCurrentLocation = function() {
        return  window.location.href;
    }

    $scope.poll = function(id) {

        console.log("Polling for ID: "+id);

        // Call the API
        $http({method: 'GET', url: $scope.POLL_API+id
        }).then(
            function success(response) {

                $scope.state.email = response.data.notifyTo;
                $scope.state.jsonAddress = response.data.jsonAddress;
                $scope.state.virusVizAddress = response.data.virusVizAddress;

                if("parsedSequences" in response.data)
                    $scope.state.numSequences  = response.data.parsedSequences;

                var startedAt =  parseInt(response.data.startedAt);
                var elapsed = (new Date().getTime() - startedAt)/1000;
                var timeTotal= $scope.state.numSequences*$scope.MINUTES_PER_SEQ*60;
                var timeleft = parseInt(timeTotal-elapsed);
                var leftPerc = Math.floor((timeleft/timeTotal)<0?0:(timeleft/timeTotal)*100);

                $("#progressBar").css("width",leftPerc+"%");
                $("#progressBar").text(leftPerc+"%");


                if( response.data.ready == true) {
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
                if(response.status==404) {
                    var message = "The result for this computation is no more available.";
                    bootbox.confirm(message, function (result) {
                        $scope.reset();
                    })
                }

            });

    }

    $scope.checkFasta = function checkFasta(d) {

        let fastaFile = document.getElementById("fasta");
        console

        if (fastaFile.files.length>0) {

            let fastaReader = new FileReader();

            fastaReader.onloadend = function (e_fasta) {
                let fastaText = e_fasta.target.result;
                $scope.$apply( a => {
                        $scope.state.numSequences = (fastaText.match(/>/g) || []).length;
                        console.log($scope.state.numSequences, "sequences found.");
                    }
                );

            }

            fastaReader.readAsText(fastaFile.files[0]);
        }
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

                    let metaText = e_meta.target.result;

                    let requestBody = {
                        emailAddress: $scope.state.email,
                        fastaText: fastaText,
                        metaText: metaText
                    }

                    $scope.upload(requestBody);

                }
                metaReader.readAsText(metaFile.files[0]);
            }
            fastaReader.readAsText(fastaFile.files[0]);
        }
    }


    $scope.submitVCF = function() {

        console.log("submit VCF");

        let jsonFile = document.getElementById('json');

        if (jsonFile.files.length === 0)
            bootbox.alert("Please, select a JSON");

        else {

            let jsonReader = new FileReader();

            jsonReader.onloadend = function (e_json) {

                console.log("JSON was read.")

                let jsonText = e_json.target.result;

                let requestBody = {
                    json: jsonText
                }

                $http({
                    method: 'POST',
                    data: $.param(requestBody),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    url: $scope.VCF_API
                }).then(
                    function success(response) {

                        var id = response.data.id;

                        // Call the API
                        $scope.pollVCF = function (id) {
                            $http({
                                method: 'GET', url: $scope.POLL_VCF_API + id
                            }).then(
                                function success(response) {
                                    console.log(response);
                                    if (response.data.ready == true) {
                                        console.log("downloading");


                                        $http.get($scope.VCF_API+id, {responseType:'arraybuffer'
                                        })
                                            .then(function (response) {

                                                var saveBlob = (function () {
                                                    var a = document.createElement("a");
                                                    document.body.appendChild(a);
                                                    a.style = "display: none";
                                                    return function (blob, fileName) {
                                                        var url = window.URL.createObjectURL(blob);
                                                        a.href = url;
                                                        a.download = fileName;
                                                        a.click();
                                                        window.URL.revokeObjectURL(url);
                                                    };
                                                }());

                                                var file = new Blob([response], {type: 'application/gzip'});

                                                saveBlob(file, "variants.vcf.gz");



                                            });
                                    } else if (response.data.failed) {
                                        console.log("error");
                                        bootbox.alert("Error: " + response.data.failedMessage);
                                    } else {
                                        console.log("polling");
                                        $timeout($scope.pollVCF, $scope.POLLING_TIMEOUT, true, id);
                                    }
                                },
                                function error(response) {

                                    var message = "The result for this computation is no more available.";
                                    bootbox.confirm(message, function (result) {
                                    });

                                });
                        }
                        $scope.pollVCF(id);




                    }
                    ,
                    function error(response) {
                        bootbox.alert("An error occurred. Response status: " + response.statusText + ".");
                    }
                );


            }

            jsonReader.readAsText(jsonFile.files[0]);
        }
    }

    $scope.$on('$routeChangeSuccess', function() {

            if ("id" in $routeParams) {
                //console.log("found id "+$routeParams["id"]);
                $scope.state.resultId = $routeParams["id"];
                $scope.state.processing = true;
                $scope.poll($scope.state.resultId);
            }
        }
    );


});