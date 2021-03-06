#!/usr/bin/env python

from modeller import *
from modeller.automodel import *
from modeller.scripts import complete_pdb
import os
import IMP.em
import IMP.multifit

os.chdir('output')

env = environ()
env.io.atom_files_directory = ['../data/templates']
env.libs.topology.read(file='$(LIB)/top_heav.lib')
env.libs.parameters.read(file='$(LIB)/par.lib')
a = automodel(env, alnfile='groel-1iokA.ali',
              knowns='1iok', sequence='P0A6F5',
              assess_methods=assess.DOPE)
a.starting_model = 1
a.ending_model = 10
a.make()

# Get a list of all successfully built models from a.outputs

ok_models = filter(lambda x: x['failure'] is None, a.outputs)

#truncated the models, as residues 524-548 were not covered by the template
truncated_models_fn=[]
full_model_norm_dope_scores=[]
for ok_model in ok_models:
    mdl_fn=ok_model['name']
    mdl = complete_pdb(env, mdl_fn)
    full_model_norm_dope_scores.append(mdl.assess_normalized_dope())
    sel=selection(mdl.residue_range(1,524))
    truncated_fn=mdl_fn.split(".pdb")[0]+".truncated.pdb"
    sel.write(truncated_fn)
    truncated_models_fn.append(truncated_fn)

norm_dope_scores=[]
fitting_scores=[]
# score models by normalized dope
for mdl_fn in truncated_models_fn:
    # Read a model previously generated by Modeller's automodel class
    mdl = complete_pdb(env, mdl_fn)
    norm_dope_scores.append(mdl.assess_normalized_dope())

# score models by em
dmap=IMP.em.read_map("groel_subunit_11.mrc",IMP.em.MRCReaderWriter())
dmap.get_header_writable().set_resolution(11.5)
imp_mdl=IMP.Model()
rb_refiner=IMP.core.LeavesRefiner(IMP.atom.Hierarchy.get_traits())
for mdl_fn in truncated_models_fn:
    print "====fitting model",mdl_fn
    #load the template
    mh=IMP.atom.read_pdb(mdl_fn,imp_mdl)
    IMP.atom.add_radii(mh)
    rb=IMP.atom.setup_as_rigid_body(mh)
    sols=IMP.multifit.pca_based_rigid_fitting(rb,rb_refiner,dmap,0.02)
    #refine the top fit
    IMP.core.transform(rb,sols.get_transformation(0))
    '''
    refined_sols = IMP.em.local_rigid_fitting(
        rb,rb_refiner,
        IMP.atom.Mass.get_mass_key(),dmap,[],1,1)
    '''
    refined_sols = IMP.em.FittingSolutions()
    refined_sols.add_solution(IMP.algebra.get_identity_transformation_3d(),
                              sols.get_score(0))
    #write the fitted model
    IMP.core.transform(rb,refined_sols.get_transformation(0))
    IMP.atom.write_pdb(IMP.atom.Hierarchy(rb),
                       mdl_fn.split(".pdb")[0]+".fitted.pdb")
    IMP.core.transform(rb,refined_sols.get_transformation(0).get_inverse())
    IMP.core.transform(rb,sols.get_transformation(0).get_inverse())
    fitting_scores.append(1.-refined_sols.get_score(0))

#print model names and their scores into a output file
output=open("model_building.scores.output","w")
output.write('%(a)-40s%(b)-25s%(c)-25s%(d)-25s\n'%{'a':"name",'b':"full model norm_dope",'c':"truncated model norm_dope",'d':"cc"})
for i ,mdl_fn in enumerate(truncated_models_fn):
    output.write('%(a)-40s%(b)-25.3f%(c)-25.3f%(d)-25.3f\n'%{'a':mdl_fn,'b':full_model_norm_dope_scores[i],'c':norm_dope_scores[i],'d':fitting_scores[i]})
output.close()
