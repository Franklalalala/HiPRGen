with (import <nixpkgs> {});


let
  pythonEnv = python38.withPackages (
      ps: [ ps.pymatgen
            ps.monty
            ps.numpy
            ps.scipy
            ps.openbabel-bindings
            ps.pygraphviz
            ps.mpi4py
          ]);
in mkShell rec {
  buildInputs = [ pythonEnv
                  sqlitebrowser
                  texlive.combined.scheme-small
                  mpi
                  (import ./RNMC.nix)
                ];
}
