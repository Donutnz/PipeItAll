"""This file acts as the main module for this script.

1. Ask for pipe diameter
2. Get all selections
3. iterate thru and find curves/lines/etc. (things that can be piped along)
4. Pipe that shiiii

"""

import traceback
import adsk.core
import adsk.fusion
# import adsk.cam

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface


def run(_context: str):
	"""This function is called by Fusion when the script is run."""

	try:
		# Your code goes here.
		#ui.messageBox(f'"{app.activeDocument.name}" is the active Document.')
		design=adsk.fusion.Design.cast(app.activeProduct)

		if not design:
			ui.messageBox('No active Fusion design', 'No Design')
			return
		
		#Get section size
		(diamInput, isCancelled) = ui.inputBox("Pipe Section Diameter: ", "Pipe Size", "10")
		
		if isCancelled:
			return
		
		diameterValue=None
		try:
			diameterValue=design.unitsManager.evaluateExpression(diamInput, design.unitsManager.defaultLengthUnits)
		except:
			ui.messageBox("Invalid length value: {}".format(diamInput),
				 "Input Error",
				 adsk.core.MessageBoxButtonTypes.OKButtonType,
				 adsk.core.MessageBoxIconTypes.CriticalIconType)
			return

		pipeableLines=list()

		# Filter for only sketchLines
		currentSelections:adsk.core.Selections=app.userInterface.activeSelections;
		
		for sel in currentSelections.asArray():
			s:adsk.core.Selection=adsk.core.Selection.cast(sel)

			app.log("Type: {}".format(s.entity.classType()))

			if s.entity.classType() == adsk.fusion.SketchLine.classType():
				pipeableLines.append(s.entity)

		# Make-a the pipes
		allPipes:adsk.fusion.PipeFeatures=design.rootComponent.features.pipeFeatures
		newPipes:list[adsk.fusion.PipeFeature] = list()

		for skLn in pipeableLines:
			sLine:adsk.fusion.SketchCurve=skLn

			pFeat:adsk.fusion.PipeFeatureInput=allPipes.createInput(
				adsk.fusion.Path.create(sLine, adsk.fusion.ChainedCurveOptions.noChainedCurves),
				adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
			pFeat.sectionSize=adsk.core.ValueInput.createByReal(diameterValue)

			newPipes.append(allPipes.add(pFeat))
			app.log("Add Pipe: {}".format(pFeat))

		app.log("Done")
			
	except:  #pylint:disable=bare-except
		# Write the error message to the TEXT COMMANDS window.
		app.log(f'Failed:\n{traceback.format_exc()}')
