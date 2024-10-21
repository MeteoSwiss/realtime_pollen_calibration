#!/bin/bash
#
# Create conda environment with pinned or unpinned requirements


if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  echo "Please simply call the script instead of sourcing it!"
  return
fi

# Default env names
DEFAULT_ENV_NAME="RTcal"

# Default options
ENV_NAME="${DEFAULT_ENV_NAME}"
PYVERSION=3.10
PINNED=true
EXPORT=false
CONDA=conda
HELP=false

help_msg="Usage: $(basename "${0}") [-n NAME] [-p VER] [-u] [-e] [-h]

Options:
 -n NAME    Env name [default: ${DEFAULT_ENV_NAME}
 -p VER     Python version [default: ${PYVERSION}]
 -u         Use unpinned requirements (minimal version restrictions)
 -e         Export environment files (requires -u)
 -h         Print this help message and exit
"

# Eval command line options
while getopts n:p:defhimu flag; do
    case ${flag} in
        n) ENV_NAME=${OPTARG};;
        p) PYVERSION=${OPTARG};;
        e) EXPORT=true;;
        h) HELP=true;;
        u) PINNED=false;;
        ?) echo -e "\n${help_msg}" >&2; exit 1;;
    esac
done

if ${HELP}; then
    echo "${help_msg}"
    exit 0
fi

echo "Setting up environment for installation"
eval "$(conda shell.bash hook)" || exit
conda activate || exit

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
echo 'Setting FIELDEXTRA_PATH for balfrin'
${CONDA} env config vars set FIELDEXTRA_PATH=/users/oprusers/osm/bin/fieldextra


echo "Variables saved to environment: "
${CONDA} env config vars list

echo -e "\n "\
    "\e[32mThe setup script completed successfully! \n \e[0m" \
    "\e[32mYou can activate you environment by running: \n \e[0m" \
    "\n "\
    "\e[32m            conda activate ${ENV_NAME} \n \e[0m"\
    " "
