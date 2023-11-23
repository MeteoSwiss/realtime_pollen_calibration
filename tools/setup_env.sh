#!/bin/bash
#
# Create conda environment with pinned or unpinned requirements
#
# - 2022-08 (D. Regenass) Write original script
# - 2022-09 (S. Ruedisuehli) Refactor; add some options
#

# Default env names
DEFAULT_ENV_NAME="RTcalib"

# Default options
ENV_NAME="${DEFAULT_ENV_NAME}"
PYVERSION=3.10
PINNED=true
EXPORT=false
CONDA=conda
HELP=false

help_msg="Usage: $(basename "${0}") [-n NAME] [-p VER] [-u] [-e] [-m] [-h]

Options:
 -n NAME    Env name [default: ${DEFAULT_ENV_NAME}
 -p VER     Python version [default: ${PYVERSION}]
 -u         Use unpinned requirements (minimal version restrictions)
 -e         Export environment files (requires -u)
 -m         Use mamba instead of conda
 -h         Print this help message and exit
"

# Eval command line options
while getopts n:p:defhimu flag; do
    case ${flag} in
        n) ENV_NAME=${OPTARG};;
        p) PYVERSION=${OPTARG};;
        e) EXPORT=true;;
        h) HELP=true;;
        m) CONDA=mamba;;
        u) PINNED=false;;
        ?) echo -e "\n${help_msg}" >&2; exit 1;;
    esac
done

if ${HELP}; then
    echo "${help_msg}"
    exit 0
fi

echo "Setting up environment for installation"
eval "$(conda shell.bash hook)" || exit  # NOT ${CONDA} (doesn't work with mamba)
conda activate || exit # NOT ${CONDA} (doesn't work with mamba)

# Create new env; pass -f to overwriting any existing one
echo "Creating ${CONDA} environment"
${CONDA} create -n ${ENV_NAME} python=${PYVERSION} --yes || exit

# Install requirements in new env
if ${PINNED}; then
    echo "Pinned installation"
    ${CONDA} env update --name ${ENV_NAME} --file requirements/environment.yml || exit
else
    echo "Unpinned installation"
    ${CONDA} env update --name ${ENV_NAME} --file requirements/requirements.yml || exit
    if ${EXPORT}; then
        echo "Export pinned prod environment"
        ${CONDA} env export --name ${ENV_NAME} --no-builds | \grep -v '^prefix:' > requirements/environment.yml || exit
    fi
fi


# Cosmo eccodes definitions
definition_version="v2.25.0.2"
conda activate ${ENV_NAME}
conda_eccodes=${CONDA_PREFIX}/share/eccodes-cosmo-resources_${definition_version}
git clone -b ${definition_version} https://github.com/COSMO-ORG/eccodes-cosmo-resources.git ${conda_eccodes} || exit
${CONDA} env config vars set GRIB_DEFINITION_PATH=${conda_eccodes}/definitions/:${CONDA_PREFIX}/share/eccodes/definitions


# fieldextra path
if [[ $(hostname -s) == *'tsa'* ]]; then
    echo 'Setting FIELDEXTRA_PATH for tsa'
    ${CONDA} env config vars set FIELDEXTRA_PATH=/project/s83c/fieldextra/tsa/bin/fieldextra_gnu_opt_omp

elif [[ $(hostname -s) == *'daint'* ]]; then
    echo 'Setting FIELDEXTRA_PATH for daint'
    ${CONDA} env config vars set FIELDEXTRA_PATH=/project/s83c/fieldextra/daint/bin/fieldextra_gnu_opt_omp

elif [[ $(hostname -s) == *'balfrin'* ]]; then
    echo 'Setting FIELDEXTRA_PATH for balfrin'
    ${CONDA} env config vars set FIELDEXTRA_PATH=/users/oprusers/osm/bin/fieldextra
fi


# # cartopy setup
# if [[ $(cp requirements/siteconfig.py $CONDA_PREFIX/lib/$python_lib/site-packages/cartopy) ]]; then
#     echo 'Cartopy configuration completed successfully.'
# else
#     echo -e "\e[31mEnable cartopy to modify cartopy.config by placing the env/siteconfig.py file into cartopy package source folder.\n\e[0m"\
#         "\e[31mPlease make sure that you are in the parent directory of the iconarray folder while executing this setup script.\e[0m"
#     exit $1
# fi


echo "Variables saved to environment: "
${CONDA} env config vars list

echo -e "\n "\
    "\e[32mThe setup script completed successfully! \n \e[0m" \
    "\e[32mYou can activate you environment by running: \n \e[0m" \
    "\n "\
    "\e[32m            conda activate ${ENV_NAME} \n \e[0m"\
    " "
