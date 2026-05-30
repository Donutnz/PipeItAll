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

		app.log("Starting Pipe! It! All! script...")

		if not design:
			ui.messageBox('No active Fusion design', 'No Design')
			return

		#Get current selected items
		currentSelections:adsk.core.Selections=app.userInterface.activeSelections

		#Check if anything is selected
		if len(currentSelections) < 1:
			ui.messageBox("Nothing Selected",
				 "Selection Error",
				 adsk.core.MessageBoxButtonTypes.OKButtonType,
				 adsk.core.MessageBoxIconTypes.CriticalIconType)
			return
		
		#Get section size
		(diamInput, isCancelled) = ui.inputBox("Pipe Section Diameter: ", "Pipe Size", "100mm")
		
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
		app.log("Filtering for valid lines...")

		for sel in currentSelections.asArray():
			s:adsk.core.Selection=adsk.core.Selection.cast(sel)

			#app.log("Type: {}".format(s.entity.classType()))

			if isinstance(s.entity,adsk.fusion.SketchCurve) or s.entity.classType() == adsk.fusion.BRepEdge.classType():
				pipeableLines.append(s.entity)

		#Break if nothing to be piped
		if len(pipeableLines) < 1:
			ui.messageBox("Nothing Pipeable Selected",
				 "Selection Error",
				 adsk.core.MessageBoxButtonTypes.OKButtonType,
				 adsk.core.MessageBoxIconTypes.CriticalIconType)
			return
		

		# Make-a the pipes
		allPipes:adsk.fusion.PipeFeatures=design.activeComponent.features.pipeFeatures
		newPipes:adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()

		tmeLnStartIdx=None
		
		app.log("Laying Pipe...")

		lnsPipedCnt=0

		progDlg=ui.createProgressDialog()
		progDlg.cancelButtonText = "Cancel"
		progDlg.isBackgroundTranslucent=False
		progDlg.isCancelButtonShown = True

		progDlg.show("Pipeing...",
			   "Completed: %p, Piped: %v, Total Pipes: %m",
			   0,
			   len(pipeableLines),
			   0
			   )

		for skLn in pipeableLines:
			sLine:adsk.fusion.SketchCurve=skLn

			if progDlg.wasCancelled:
				break

			pipePath:adsk.fusion.Path=adsk.fusion.Path.create(sLine, adsk.fusion.ChainedCurveOptions.noChainedCurves)

			pFeat:adsk.fusion.PipeFeatureInput=allPipes.createInput(
				pipePath,
				adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
			
			pFeat.sectionSize=adsk.core.ValueInput.createByReal(diameterValue)

			curPipe=design.activeComponent.features.pipeFeatures.add(pFeat)

			#Grab first timeline index
			if tmeLnStartIdx is None:
				tmeLnStartIdx=curPipe.timelineObject.index

			newPipes.add(curPipe.bodies.item(0))

			lnsPipedCnt+=1

			if lnsPipedCnt % 10 == 0:
				adsk.doEvents()
			
			app.log("Add Pipe: {}".format(curPipe.name))
			progDlg.progressValue=lnsPipedCnt

		progDlg.hide()

		"""

		#Combine all created pipe bodies
		app.log("Combining Pipes...")

		targetPipe=newPipes.item(0) #Use first pipe as target body
		newPipes.removeByIndex(0)

		combinePipesInp:adsk.fusion.CombineFeatureInput=design.rootComponent.features.combineFeatures.createInput(targetPipe, newPipes)
		combinePipesInp.operation=adsk.fusion.FeatureOperations.JoinFeatureOperation
		
		tmeLnEndIdx=design.rootComponent.features.combineFeatures.add(combinePipesInp).timelineObject.index

		#Group timeline objects (for tidyness)
		app.log("Grouping Features...")

		pipeGroup=design.timeline.timelineGroups.add(tmeLnStartIdx, tmeLnEndIdx)
		pipeGroup.name="PipeNetwork"

		"""

		app.log("Done")
			
	except:  #pylint:disable=bare-except
		# Write the error message to the TEXT COMMANDS window.
		app.log(f'Failed:\n{traceback.format_exc()}')
