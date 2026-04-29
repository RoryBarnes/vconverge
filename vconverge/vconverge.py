import os
import subprocess
import sys
from astropy.io import ascii
#import corner
import numpy as np
import re
import shutil
import bigplanet as bp
import json
import copy
from scipy.stats import ks_2samp
from scipy.special import kl_div
#import matplotlib.pyplot as plt
#import vspace

# Parameter sweep until user defined params converge

def extract_info_vcnv(vcnvFile):
	vcnv = open(vcnvFile, 'r')
	lines = vcnv.readlines()
	params_to_conv = []
	hold = []
	sConvergenceMethod = 'KL'
	iBaseSeed = None
	for i in range(len(lines)):
		if lines[i].split() == []:
			pass
		elif lines[i].split()[0] == 'sVspaceFile':
			vspFi = lines[i].split()[1]
		elif lines[i].split()[0] == 'iStepSize':
			StepSize = int(lines[i].split()[1])
		elif lines[i].split()[0] == 'iMaxSteps':
			MaxSteps = int(lines[i].split()[1])
		elif lines[i].split()[0] == 'sConvergenceMethod':
			ConvMethod = lines[i].split()[1]
		elif lines[i].split()[0] == 'fConvergenceCondition':
			ConvCondit = float(lines[i].split()[1])
		elif lines[i].split()[0] == 'iNumberOfConvergences':
			ConvNum = int(lines[i].split()[1])
		elif lines[i].split()[0] in ('iSeed', 'seed'):
			if not float(lines[i].split()[1]).is_integer():
				raise IOError('iSeed in %s must be an integer; got %s' % (vcnvFile, lines[i].split()[1]))
			iBaseSeed = int(lines[i].split()[1])
		elif lines[i].split()[0] == 'sObjectFile':
			if hold != [] and len(hold) > 1:
				params_to_conv.append(hold)
			hold = []
			hold.append(lines[i].split()[1])
		elif lines[i].split()[0] == 'saConverge':
			if len(lines[i].split()) != 3:
				raise IOError('Regarding line: %s Please be sure to only specify final/initial after saConverge, then the name of the param to converge, vconverge\'s saConverge option cannot accept any more or less than these inputs' % lines[i])
			if lines[i].split()[1] != 'final' and lines[i].split()[1] != 'initial':
				raise IOError('Formatting of line: %s Is incorrect, please use: saConverge [initial/final] [name of param to converge]' % lines[i])
			if hold == []:
				raise IOError('Please specify the body you would like %s to converge for' % lines[i].split()[2])
			param = lines[i].split()[2]+','+lines[i].split()[1]
			hold.append(param)
	if hold != [] and len(hold) > 1:
		params_to_conv.append(hold)

	return vspFi, StepSize, MaxSteps, ConvMethod, ConvCondit, ConvNum, params_to_conv, iBaseSeed

def extract_info_vsp(vspFile): # Extracts relevant info from vspace.in file for vconverge including srcfolder, destfolder, and predefined prior file info (if applicable)
	vspog = open(vspFile, 'r')
	linesog = vspog.readlines()
	PrimeFi = 'vpl.in'
	for i in range(len(linesog)):
		if linesog[i].split() == []:
			pass
		elif linesog[i].split()[0] in ('srcfolder', 'sSrcFolder'):
			if linesog[i].split()[1] == '.': # Current working dir is srcfolder, get full path for vspacetmp srcfolder
				source_fold = os.getcwd()
			else:
				source_fold = linesog[i].split()[1]
		elif linesog[i].split()[0] in ('destfolder', 'sDestFolder'):
			dest_fold = linesog[i].split()[1]
		elif linesog[i].split()[0] in ('samplemode', 'sSampleMode'):
			modename = linesog[i].split()[1]
			if modename.startswith('r') or modename.startswith('R'):
				mode = 'random'
			else:
				raise IOError('vconverge is currently only compatible with random mode')
		elif linesog[i].split()[0] in ('randsize', 'iNumTrials'):
			initial_sim_size = int(linesog[i].split()[1])
		elif linesog[i].split()[0] in ('trialname', 'sTrialName'):
			triname = linesog[i].split()[1]
		elif linesog[i].split()[0] in ('file', 'sBodyFile', 'sPrimaryFile'):
			curr_fi = linesog[i].split()[1]
			curr_fi = curr_fi.split('.')[0]
			if linesog[i].split()[0] == 'sPrimaryFile':
				PrimeFi = linesog[i].split()[1]

	return source_fold, dest_fold, triname, PrimeFi, initial_sim_size#, prior_files, prior_vars, prior_vars_cols
			

def fnInjectSeedIntoVspaceFile(sInputPath, sOutputPath, iSeed): # Copy a vspace.in to a new path, stripping any iSeed/seed lines and appending iSeed <iSeed>.
	vspog = open(sInputPath, 'r')
	linesog = vspog.readlines()
	vspog.close()
	vsptmp = open(sOutputPath, 'w')
	for i in range(len(linesog)):
		if linesog[i].split() == []:
			vsptmp.write(linesog[i])
		elif linesog[i].split()[0] in ('iSeed', 'seed'):
			continue
		else:
			vsptmp.write(linesog[i])
	vsptmp.write('iSeed '+str(int(iSeed))+'\n')
	vsptmp.close()

def create_tmp_vspin(vspFile, RunIndex, stepsize, iBaseSeed=None): # Creates a temporary vspace.in file to run for steps subsequent to original run
	vspog = open(vspFile, 'r') # Read in original (og) vspace file provided as input by user
	linesog = vspog.readlines()
	vspog.close()
	predefpriors_used = False
	vsptmp = open('vconverge_tmp/vspace_tmp.in', 'w') # Create new temp vspace file in vconverge tmp directory
	for i in range(len(linesog)):
		if linesog[i].split() == []:
			pass
		elif linesog[i].split()[0] in ('iSeed', 'seed'):
			continue # vconverge owns the seed; skip any user-provided value in vspace.in
		elif linesog[i].split()[0] in ('destfolder', 'sDestFolder'):
			sKeyword = linesog[i].split()[0]
			vsptmp.write(sKeyword+' vconverge_tmp/Step_'+str(RunIndex)+'\n')
		elif linesog[i].split()[0] in ('trialname', 'sTrialName'):
			sKeyword = linesog[i].split()[0]
			vsptmp.write(sKeyword+' Step'+str(RunIndex)+'_'+linesog[i].split()[1]+'\n')
		elif linesog[i].split()[0] in ('randsize', 'iNumTrials'):
			sKeyword = linesog[i].split()[0]
			vsptmp.write(sKeyword+' '+str(stepsize)+'\n')
		elif re.search("\[", linesog[i]) != None: # look for predefined prior files, change to tmp name
			spl = re.split("[\[\]]", linesog[i])
			var = spl[0].strip() # Current variable
			values = spl[1].split(",")
			for j in range(len(values)):
				values[j] = values[j].strip()
			if values[2][0] == 'p':
				predefpriors_used = True
				priorhold = values[0].split('/')
				tmpprior = priorhold[len(priorhold)-1]
				tmpprior = 'tmp_'+tmpprior
				vsptmp.write(var+' [vconverge_tmp/'+tmpprior+', '+values[1]+', '+values[2]+', '+values[3]+'] '+spl[2].strip()+'\n')
			else:
				vsptmp.write(linesog[i]+'\n')
		else:
			vsptmp.write(linesog[i]+'\n')
	if iBaseSeed is not None:
		vsptmp.write('iSeed '+str(int(iBaseSeed) + int(RunIndex))+'\n')
	vsptmp.close()
	return predefpriors_used


def create_tmp_prior_files(RunIndex, og_triname, dst_fold): # Create new prior files deleting previously used priors
	if RunIndex == 1:
		prev = open(os.path.join(dst_fold, og_triname+'PriorIndicies.json'), 'r')
	else:
		prev = open(os.path.join(dst_fold, 'Step_'+str(RunIndex-1)+'/Step'+str(RunIndex-1)+'_'+og_triname+'PriorIndicies.json'), 'r')
	prev = json.load(prev)
	prev = json.loads(prev)
	for i in prev:
		finame = i.split('/')[len(i.split('/')) - 1]
		extension = finame[len(finame) - 3]+finame[len(finame) - 2]+finame[len(finame) - 1]
		if extension == 'npy':
			priorfi = np.load(i)
			newpriorfi = np.delete(priorfi, prev[i], axis=0)
			if RunIndex == 1:
				np.save('vconverge_tmp/tmp_'+finame, newpriorfi)
			else:
				np.save('vconverge_tmp/'+finame, newpriorfi)
		elif extension == 'txt' or extension == 'dat':
			priorfi = ascii.read(i)
			del(priorfi[np.array(prev[i])])
			if RunIndex == 1:
				ascii.write(priorfi, 'vconverge_tmp/tmp_'+finame, format='fixed_width', delimiter=' ', overwrite=True)
			else:
				ascii.write(priorfi, 'vconverge_tmp/'+finame, format='fixed_width', delimiter=' ', overwrite=True)

def fbCheckLogFileComplete(sLogFilePath):
	with open(sLogFilePath, 'r') as logFile:
		for sLine in logFile:
			if len(sLine.split()) > 2 and sLine.split()[1] == 'FINAL':
				return True
	return False

def flistReadValidLogFile(sLogPath):
	if not fbCheckLogFileComplete(sLogPath):
		raise IOError('Incomplete log file (no FINAL section)')
	with open(sLogPath, 'r') as logHandle:
		return logHandle.readlines()

def fiMatchBodyAndFinitIndex(daBody, daFinit, sCurrentBody, sFinitHold, daIndex):
	daBodyAtIndex = daBody[daIndex]
	daFinitAtIndex = daFinit[daIndex]
	if sCurrentBody not in daBodyAtIndex or sFinitHold not in daFinitAtIndex:
		return None
	daBodyMatches = np.where(daBodyAtIndex == sCurrentBody)[0]
	daFinitMatches = np.where(daFinitAtIndex == sFinitHold)[0]
	for iBodyMatch in daBodyMatches:
		for iFinitMatch in daFinitMatches:
			if iBodyMatch == iFinitMatch:
				return iBodyMatch
	return None

def fnExtractConvergenceValues(listLines, daBody, daVariable, daFinit, listParamsToConverge, dictConverge):
	sFinitHold = None
	sCurrentBody = None
	for i in range(len(listLines)):
		if len(listLines[i].split()) <= 2:
			continue
		if listLines[i].split()[1] == 'FINAL':
			sFinitHold = 'final'
		elif listLines[i].split()[1] == 'INITIAL':
			sFinitHold = 'initial'
		elif listLines[i].split()[1] == 'BODY:':
			sCurrentBody = listLines[i].split()[2]
		elif listLines[i].split()[0] in daVariable:
			daIndex = np.where(daVariable == listLines[i].split()[0])[0]
			iTrueIndex = fiMatchBodyAndFinitIndex(daBody, daFinit, sCurrentBody, sFinitHold, daIndex)
			if iTrueIndex is not None:
				sParamKey = np.array(listParamsToConverge)[daIndex][iTrueIndex]
				dictConverge[sParamKey].append(float(listLines[i].split()[-1]))

def ftParseLogFiles(sBaseDir, sLogFile, daBody, daVariable, daFinit, listParams, dictConverge, sDestDir=None):
	iSuccessCount = 0
	iFailedCount = 0
	for sSubdir, listDirs, listFiles in sorted(os.walk(sBaseDir), key=lambda t: t[0]):
		if sSubdir == sBaseDir:
			continue
		sLogPath = os.path.join(sSubdir, sLogFile)
		sSimName = os.path.basename(sSubdir)
		try:
			listLines = flistReadValidLogFile(sLogPath)
		except (FileNotFoundError, IOError) as error:
			print('WARNING: Skipping %s: %s' % (sSimName, str(error)))
			iFailedCount += 1
			continue
		if sDestDir is not None:
			shutil.copytree(sSubdir, os.path.join(sDestDir, sSimName))
		fnExtractConvergenceValues(listLines, daBody, daVariable, daFinit, listParams, dictConverge)
		iSuccessCount += 1
	return (iSuccessCount, iFailedCount)

def fnCheckFailureRate(iSuccessCount, iFailedCount, sStepDescription):
	iTotal = iSuccessCount + iFailedCount
	if iTotal == 0:
		raise IOError('No simulations found in %s' % sStepDescription)
	dFailureRate = iFailedCount / iTotal
	if dFailureRate > 0.5:
		raise IOError(
			'More than 50%% of vplanet simulations failed in %s '
			'(%d of %d). Check input files and model configuration.'
			% (sStepDescription, iFailedCount, iTotal))
	print('%s: %d succeeded, %d failed' % (sStepDescription, iSuccessCount, iFailedCount))

def vconverge(vcnvFile):
	# make the temporary directory and remove stale checkpoints
	if os.path.exists('vconverge_tmp'):
		shutil.rmtree('vconverge_tmp')
	if os.path.exists('.vconverge_tmp'):
		shutil.rmtree('.vconverge_tmp')
	os.mkdir('vconverge_tmp')

	# extract required info from the vconverge.in file and the vspace.in file respectively
	vspFile, StepSize, MaxSteps, ConvMethod, ConvCondit, ConvNum, params_to_conv, iBaseSeed = extract_info_vcnv(vcnvFile)
#	src_fold, dst_fold, og_triname, primeFi, pfiles, pvars, pvarscols = extract_info_vsp(vspFile)
	src_fold, dst_fold, og_triname, primeFi, initialsims = extract_info_vsp(vspFile)

	# Check that vconverge can find the files associated with the bodies that have requested converging parameters
	# These files should be among the files copied by vspace and should be found in the srcfolder defined in the vspace.in file
	for i in params_to_conv:
		if not os.path.isfile(os.path.join(src_fold, i[0])):
			raise IOError('%s does not exist. Please specify body/primary file source directories in the vspace.in file. Give only the name of the file to option sObjectFile for vconverge.' % os.path.join(src_fold, i[0]))

	# Extract the sName of the bodies for each requested converging parameter then delete the list entry containing the name of the file
	# append sName (body name that will be used by VPLanet) to each parameter associated with it to build up a string of bodyname_parametername_finalorinitial
	for i in params_to_conv:
		curr_fi = open(os.path.join(src_fold, i[0]), 'r')
		currlines = curr_fi.readlines()
		curr_fi.close()
		for k in range(len(currlines)):
			if currlines[k].split() == []:
				pass
			if currlines[k].split()[0] == 'sName':
				body = currlines[k].split()[1]
				break
		for k in range(len(i)):
			if k != 0:
				i[k] = body+','+i[k]
		i.pop(0)
	
	# turn list of lists into one single list for simplicity's sake
	hold = []
	for i in params_to_conv:
		for k in range(len(i)):
			hold.append(i[k])
	params_to_conv = hold
	del(hold)

	# Get the future name of the log files from the primary file (sSystemName + .log) 
	if not os.path.isfile(os.path.join(src_fold, primeFi)):
		raise IOError('vconverge cannot find %s. Please specify the primary file and source directory in the vspace.in file as vspace would expect it, this is also how vconverge will expect it.' % os.path.join(src_fold, primeFi))
	primefi_open = open(os.path.join(src_fold, primeFi))
	primelines = primefi_open.readlines()
	primefi_open.close()
	for i in range(len(primelines)):
		if primelines[i].split() == []:
			pass
		elif primelines[i].split()[0] == 'sSystemName':
			vplanet_logfile = primelines[i].split()[1]+'.log'
			break

	# Create a dictionary to hold the values to converge from every simulation
	converge_dict = {}
	for i in params_to_conv:
		converge_dict[i] = []

	#Run Vspace on OG
	if iBaseSeed is not None:
		fnInjectSeedIntoVspaceFile(vspFile, 'vconverge_tmp/vspace_init.in', iBaseSeed)
		subprocess.run(['vspace', '-f', 'vconverge_tmp/vspace_init.in'], check=True)
		subprocess.run(['multiplanet', '-q', '-f', 'vconverge_tmp/vspace_init.in'], check=True)
	else:
		subprocess.run(['vspace', '-f', str(vspFile)], check=True)
		subprocess.run(['multiplanet', '-q', '-f', str(vspFile)], check=True)
	#Run Multi-planet on OG
	RunIndex = 1
	predefpriors_used = create_tmp_vspin(vspFile, RunIndex, StepSize, iBaseSeed=iBaseSeed) # Make the temporary vspace file
	if predefpriors_used == True:
		create_tmp_prior_files(RunIndex, og_triname, dst_fold) # Make the temporary prior files

	# go through initial set and extract the values of the converging parameters for all sims
	body = []
	variable = []
	finit = []
	for i in params_to_conv: # extract info on the bodies, variables to converge, and whether they're final or initial
		body.append(i.split(',')[0])
		variable.append('('+i.split(',')[1]+')')
		finit.append(i.split(',')[2])

	body = np.array(body)
	variable = np.array(variable)
	finit = np.array(finit)

	iSuccess, iFailed = ftParseLogFiles(dst_fold, vplanet_logfile, body, variable, finit, params_to_conv, converge_dict)
	fnCheckFailureRate(iSuccess, iFailed, 'initial run')

	for i in params_to_conv:
		if converge_dict[i] == []:
			raise IOError(
				'%s produced no values. %d of %d simulations failed. '
				'Check parameter spelling, modules, and vplanet compatibility.'
				% (i, iFailed, iSuccess + iFailed))

	# --------------------------------------- LOOP START --------------------------------------------------
	# At this point, the initial training set has been processed and recorded. Now the loop will begin systematically adding steps of simulations of size StepSize
	# After every step, the code will check for convergence. At this point KL convergence is the only usable method, more may be added in future.
	Num_Convs = 0 # Keep track of the number of times the code reports consecutive convergence
	Totnumconvs = 0 # Keep track of total number of times convergence is reached
	quants = list(np.linspace(0.01, 0.99, 99)) # array from 0.01 to 0.99 by 0.01 for the quantile calculations
	f = open('vconverge_results.txt', 'w')
	
	while Num_Convs < ConvNum and RunIndex <= MaxSteps: # until the number of convergences has been met or the max number of allowed steps has been taken

		if ConvMethod == 'KL_Quantiles': # If convergence methods use quantiles, build up previous quantiles
			prev_quant = {} # get quantiles before next step is taken
			for i in params_to_conv:
				prev_quant[i] = np.quantile(converge_dict[i], quants)
		elif ConvMethod == 'KS_pval'or ConvMethod == 'KS_statistic': # If convergence method uses true values, save previous true values before next step
			prev_dict = copy.deepcopy(converge_dict) # deep copy so the dictionaries don't refer to the same object

		# Run Vspace
		# Run Multi-planet
		subprocess.run(['vspace', '-f', 'vconverge_tmp/vspace_tmp.in'], check=True)
		subprocess.run(['multiplanet', '-q', '-f', 'vconverge_tmp/vspace_tmp.in'], check=True)

		sStepDir = 'vconverge_tmp/Step_' + str(RunIndex)
		iStepSuccess, iStepFailed = ftParseLogFiles(sStepDir, vplanet_logfile, body, variable, finit, params_to_conv, converge_dict, sDestDir=dst_fold)
		fnCheckFailureRate(iStepSuccess, iStepFailed, 'step %d' % RunIndex)
		if ConvMethod == 'KL_Quantiles':
			curr_quant = {} # get current quantiles, after step has been taken
			for i in params_to_conv:
				curr_quant[i] = np.quantile(converge_dict[i], quants)

		f.write('\n')
		f.write('----- Step '+str(RunIndex)+' -----\n\n')
		if ConvMethod == 'KS_statistic':
			f.write('KS Statistics:\n')
		elif ConvMethod == 'KS_pval':
			f.write('KS P-Values:\n')
		elif ConvMethod == 'KL_Quantiles':
			f.write('KL Divergence:\n')

		# For the KS test, check the p-value or the ks statistic (based on user input)
		if ConvMethod == 'KS_pval' or ConvMethod == 'KS_statistic':
			ks = {}
			converged = []
			for i in params_to_conv:
				ksstat, pval = ks_2samp(prev_dict[i], converge_dict[i])
				if ConvMethod == 'KS_pval':
					ks[i] = pval
					f.write(i+' ----- '+str(pval)+'\n')
				elif ConvMethod == 'KS_statistic':
					ks[i] = ksstat
					print(i+' KS Statistic ---- '+str(ksstat))
					f.write(i+' ----- '+str(ksstat)+'\n')
				if ConvMethod == 'KS_pval' and pval >= ConvCondit:
					converged.append(True)
				elif ConvMethod == 'KS_statistic' and ksstat <= ConvCondit:
					converged.append(True)
				else:
					converged.append(False) # If even 1 parameter has not converged, it's False and break the loop

		f.write('\n')

		if False not in converged: # If all params have converged, add 1 to the Num_Convs (number of times the model has converged consecutively)
			Num_Convs = Num_Convs + 1
			Totnumconvs = Totnumconvs + 1
			f.write('Converged = True\n')
			f.write('Number of Consecutive Convergences: '+str(Num_Convs)+'\n')
		elif False in converged: # If even one param did not converged, make sure Num_Convs (number of times the model has converged consecutively) is set to 0
			Num_Convs = 0
			f.write('Converged = False\n')

		RunIndex = RunIndex + 1

		# Create new vspace.in and prior files
		predefpriors_used = create_tmp_vspin(vspFile, RunIndex, StepSize, iBaseSeed=iBaseSeed) # Make the temporary vspace file
		if predefpriors_used == True:
			create_tmp_prior_files(RunIndex, og_triname, 'vconverge_tmp') # Make the temporary prior files

	if RunIndex >= MaxSteps:
		print('MaxSteps reached')
		print('Number of Convergences: '+str(Num_Convs))


	f.write('\n')
	f.write('-------------- VCONVERGE STATS ----------------\n\n')
	f.write('Number of Steps Taken: '+str(RunIndex-1)+'\n')
	totalsims = initialsims + ((RunIndex-1)*StepSize)
	f.write('Total Number of Simulations Ran: '+str(totalsims)+'\n')
	if RunIndex < MaxSteps:
		f.write(str(ConvNum)+' Consecutive Convergences Achieved, vconverge run sucessful\n')
	else:
		f.write('Max Steps Reached. '+str(Num_Convs)+' Consecutive Convergences Achieved\n')
	f.write('Total Number of Convergences during vconverge run: '+str(Totnumconvs)+'\n')
#	if False not in converged:
#		f.write('Converged - True\n')
#	else:
#		f.write('Converged - False\n')
#	f.write('Number of Consecutive Convergences: '+str(Num_Convs)+'\n\n')
#	if ConvMethod == 'KS_pval':
#		f.write('p-values from KS Test:\n')
#	elif ConvMethod == 'KS_statistic':
#		f.write('KS Statistics from KS Test:\n')
#	if ConvMethod == 'KS_pval' or ConvMethod == 'KS_statistic':
#		for i in params_to_conv:
#			f.write(i+' ----- '+str(ks[i])+'\n')
	f.close()

	# Save dictionary of converging params
	dicthold = json.dumps(converge_dict)
	cparams = open(os.path.join(dst_fold, 'Converged_Param_Dictionary.json'), 'w')
	json.dump(dicthold, cparams)
	cparams.close()

	for i in converge_dict:
		for k in range(len(converge_dict[i])-1):
			if converge_dict[i][k] == converge_dict[i][k+1]:
				same = True
			else:
				same = False
				break
		if same == True:
			converge_dict[i][0] = converge_dict[i][0]+1e-10

        ######## UNCOMMENT BELOW FOR CORNERS PLOTS ##############

	# Group converging parameters by body for corners plotting
	#hold = []
	#for i in range(len(body)):
	#	if body[i] not in hold:
	#		hold.append(body[i])
	#groups = []
	#for i in hold:
	#	hold2 = []
	#	for k in range(len(body)):
	#		if i == body[k]:
	#			hold2.append(params_to_conv[k])
	#	groups.append(hold2)

	# Make Corners plots
	#for i in groups:
	#	currbody = i[0].split(',')[0]
	#	cornerdat = []
	#	for k in range(len(converge_dict[i[0]])):
	#		hold3 = []
	#		for j in range(len(i)):
	#			hold3.append(converge_dict[i[j]][k])
	#		cornerdat.append(hold3)
	#	fig = corner.corner(cornerdat, quantiles=[0.16, 0.5, 0.84], color='g', show_titles=True, title_fmt='.4f', labels=i)
	#	plt.savefig(os.path.join(dst_fold, currbody+'.png'))
	#	plt.close(fig)
	

	return converge_dict, converged


def main():
    if len(sys.argv) < 2:
        print("Usage: vconverge <input_file>")
        sys.exit(1)
    vconverge(sys.argv[1])

if __name__ == "__main__":
    main()
