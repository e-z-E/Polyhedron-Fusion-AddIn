import adsk.core, adsk.fusion, adsk.cam, traceback
import urllib

# Global list to keep all event handlers in scope.
handlers = []

# Dict of polyhedra shapes and their parent grouping
all_polyhedra = {
    'Platonic Solids': ['Tetrahedron',
                        'Octahedron',
                        'Cube',
                        'Icosahedron',
                        'Dodecahedron'],
    'Archimedean Solids':['TruncatedTetrahedron',
                        'Cuboctahedron',
                        'TruncatedOctahedron',
                        'TruncatedCube',
                        'Rhombicuboctahedron',
                        'LsnubCube',
                        'RsnubCube',
                        'Icosidodecahedron',
                        'TruncatedCuboctahedron',
                        'TruncatedIcosahedron',
                        'TruncatedDodecahedron',
                        'Rhombicosidodecahedron',
                        'LsnubDodecahedron',
                        'RsnubDodecahedron',
                        'TruncatedIcosidodecahedron'],
    'Catalan Solids': ['TriakisTetrahedron',
                        'RhombicDodecahedron',
                        'TetrakisHexahedron',
                        'TriakisOctahedron',
                        'DeltoidalIcositetrahedron',
                        'RpentagonalIcositetrahedron',
                        'LpentagonalIcositetrahedron',
                        'RhombicTriacontahedron',
                        'DisdyakisDodecahedron',
                        'PentakisDodecahedron',
                        'TriakisIcosahedron',
                        'DeltoidalHexecontahedron',
                        'RpentagonalHexecontahedron',
                        'LpentagonalHexecontahedron',
                        'DisdyakisTriacontahedron'],
    'Kepler-Poinsot Solids':['SmallStellatedDodecahedron',
                        'GreatStellatedDodecahedron',
                        'GreatDodecahedron',
                        'GreatIcosahedron']
}

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions
        
        # Create a button command definition.
        button = cmdDefs.addButtonDefinition('PolyhedronButtonDefId', 
                                                   'Polyhedron Generator', 
                                                   'Need a tooltip',
                                                   './resources')
        
        # Connect to the command created event.
        polyCommandCreated = PolyCommandCreatedEventHandler()
        button.commandCreated.add(polyCommandCreated)
        handlers.append(polyCommandCreated)
        
        # Get the create panel in the model workspace. 
        addInsPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        
        # Add the button to the bottom of the panel.
        buttonControl = addInsPanel.controls.addCommand(button)

        ui.messageBox("The Polyhedron Button is located in the Solid -> Create dropdown menu.")
        ui.messageBox("This AddIn requires an internet connection to grab shape information from dmccooey.com/polyhedra")
                    
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the commandCreated event.
class PolyCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            ui = app.userInterface
            
            # Get the command
            cmd = eventArgs.command

            # Get the CommandInputs collection to create new command inputs.            
            inputs = cmd.commandInputs

            # Create dropdown list to select polyhedron grouping
            group = inputs.addDropDownCommandInput('polygroup', 'Polyhedron Group', 1)
            dropdownItems1 = group.listItems
            dropdownItems1.add('Platonic Solids', True, '')
            dropdownItems1.add('Archimedean Solids', False, '')
            dropdownItems1.add('Catalan Solids', False, '')
            dropdownItems1.add('Kepler-Poinsot Solids', False, '')
            #dropdownItems1.add('Versi-Regular Polyhedra', False, '')
            dropdownItems1.add('Custom Link', False, '')

            # Create dropdown list to select a solid. 
            polyhedronInput = inputs.addDropDownCommandInput('solid_select', 'Select Polyhedron', 1)
            dropdownItems2 = polyhedronInput.listItems
            dropdownItems2.add('Tetrahedron', True, '')
            dropdownItems2.add('Octahedron', False, '')
            dropdownItems2.add('Cube', False, '')
            dropdownItems2.add('Icosahedron', False, '')
            dropdownItems2.add('Dodecahedron', False, '')

            # Create a string input to get the weblink for polyhedron coordinates
            linkInput = inputs.addStringValueInput('link', 'Link', r'http://dmccooey.com/polyhedra/Icosahedron.txt')
            linkInput.isVisible = False

            # Create textbox to give link to website for more polyhedra
            textInput = inputs.addTextBoxCommandInput('text', 'Note', 'Select a polyhedron from a grouping   OR   Browse <a href="http://dmccooey.com/polyhedra">David McCooey\'s polyhedra website</a> for more polyhedra! Select "Custom Link" drop down to input the URL for your shape.', 3, True)

            # Connect to the execute event.
            onExecute = PolyCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            # Connect to the inputChanged event.
            onInputChanged = PolyCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
        except:
            if ui:
                ui.messageBox('Failed: {}'.format(traceback.format_exc()))
        

# Event handler for the inputChanged event.
class PolyCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input

            # Check if the polyhedron grouping input changed
            if changedInput.id == 'polygroup':
                # Get name of slected grouping
                group_name = changedInput.selectedItem.name
                # Get the input controls for custom link and solid select
                inputs = eventArgs.firingEvent.sender.commandInputs
                linkInput = inputs.itemById('link')
                polyhedronInput = inputs.itemById('solid_select')

                # Change the visibility of the custom link input.
                if group_name == 'Custom Link':
                    linkInput.isVisible = True
                else:
                    linkInput.isVisible = False

                # Change the solid select drop down menu for polyhedra grouping
                if group_name in all_polyhedra.keys():
                    # Remove all list items from current dropdown
                    dropdownItems = polyhedronInput.listItems
                    dropdownItems.clear()

                    # Repopulate dropdown list with new grouping of shapes
                    for shape in all_polyhedra[group_name]:
                        dropdownItems.add(shape, False, '')
                    # Select the first item from the new populated list
                    dropdownItems.item(0).isSelected = True

                    polyhedronInput.isVisible = True
                else:
                    polyhedronInput.isVisible = False

        except:
            if ui:
                ui.messageBox('Failed: {}'.format(traceback.format_exc))


# Event handler for the execute event.
class PolyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Get the values from the command inputs.
            inputs = eventArgs.command.commandInputs

            polygroup = inputs.itemById('polygroup').selectedItem.name

            # Check if custom link has been selected
            if polygroup == 'Custom Link':
                link = inputs.itemById('link').value

                # Fix link if html is submitted instead of txt
                if link.endswith('.html'):
                    link = link[:-4] + 'txt'

                # Check if link connects to the correct website
                if not link.startswith(r'http://dmccooey.com/polyhedra'):
                    if ui:
                        ui.messageBox('Custom link should access dmccooey.com/polyhedra')
                        return
            
            # If custom name is not selected, build weblink from polyhedron name
            else:
                name = inputs.itemById('solid_select').selectedItem.name
                link = r'http://dmccooey.com/polyhedra/' + name + '.txt'

            # send link to function to build the shape 
            makePoly(link)   

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def makePoly(link):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Check if link can connect and receive data
        try:
            content = urllib.request.urlopen(link)
            content = [line.decode().strip() for line in content]
            content = [line for line in content if line is not '']
        except:
            if ui:
                ui.messageBox('Problem with connecting to web data')
            return

        # Decode data into lists for constants, vertices, and faces
        poly_name = content.pop(0)
        constants = {}  # TO DO: Clean up constants with ordered dict
        c_keys = []
        vertices = []
        faces = []

        # Loop through every line in shape information
        for line in content:
            if line[0] == 'C':
                C_name, val = line.split(' = ')[:2]
                key = C_name.strip(' ')
                # Check for repeated constants. Some files have equation listed on seperate lines. 
                if key in constants:
                    continue
                constants[key] = val
                c_keys.insert(0, key)

            elif line[0] == 'V':
                name, val = line.strip(')').split(' = (')
                if c_keys:
                    for key in c_keys:
                        val = val.replace(key, constants[key])
                val1, val2, val3 = (val.split(','))
                vertices.append([val1, val2, val3])

            elif line[0] == r'{':

                vals = line.strip('{').strip('}').split(', ')
                faces.append(vals)

            ###############

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)

        # Get the root component of the active design
        rootComp = design.rootComponent

        allOccs = rootComp.occurrences
        transform = adsk.core.Matrix3D.create()  # Not sure what this is for

        timeline_start = adsk.fusion.Timeline.markerPosition

        # Create component for polyhedron
        occ1 = allOccs.addNewComponent(transform)
        subComp1 = occ1.component
        subComp1.name = poly_name

        # Get sketches and a base plane
        sketches = subComp1.sketches
        xyPlane = rootComp.xYConstructionPlane

        # 
        surfaces = adsk.core.ObjectCollection.create()
        profiles_collection = adsk.core.ObjectCollection.create()
        patches = subComp1.features.patchFeatures

        # Loop through each face profile to be created from 'faces' list
        for face in faces:
            # Get new sketch ready to create a profile
            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            profiles_collection = adsk.core.ObjectCollection.create()

            # For each pair of verteces in the face, draw a line
            for i in range(len(face)):
                point1 = vertices[int(face[i])]
                point2 = vertices[int(face[i-1])]
                point1 = [float(x) for x in point1]  # TO DO: Check if float is needed
                point2 = [float(x) for x in point2]
                lines.addByTwoPoints(adsk.core.Point3D.create(point1[0], point1[1], point1[2]),
                adsk.core.Point3D.create(point2[0], point2[1], point2[2]))

            # Grab all profiles in the face for creating patch
            for profile in sketch.profiles:
                profiles_collection.add(profile)

            # Create a surface patch from sketch profiles; creates one face of polyhedron
            patch_input = patches.createInput(profiles_collection, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            patch_feature = patches.add(patch_input)
            patch_feature.bodies.item(0).isLightBulbOn = False

            # Add new patch to the surfaces collection
            surfaces.add(patch_feature.bodies[0])
        
        # Boundary fill on all features to create solid
        bfill = subComp1.features.boundaryFillFeatures
        bfill_input = bfill.createInput(surfaces, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        # Select all cells in boundary fill operation 
        for cell in bfill_input.bRepCells:
            cell.isSelected = True
        bfill.add(bfill_input)  # TO DO: remove tools when bfill

        """
        # Create timeline group for all operations
        timeline_end = adsk.fusion.Timeline.markerPosition
        timeline = design.timeline.timelineGroups
        timeline.add((timeline_start, timeline_end))
        """

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Clean up the UI.
        cmdDef = ui.commandDefinitions.itemById('PolyhedronButtonDefId')
        if cmdDef:
            cmdDef.deleteMe()
            
        addinsPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        cntrl = addinsPanel.controls.itemById('PolyhedronButtonDefId')
        if cntrl:
            cntrl.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	