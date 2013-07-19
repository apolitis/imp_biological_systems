#!/usr/bin/env python

import unittest
import sys
import os
import subprocess

class Tests(unittest.TestCase):

    def test_comparative_modeling(self):
        """Test the comparative modeling script"""
        # Make sure the script runs without errors
        p = subprocess.check_call(['./model_mult.py', '--run_quick_test'],
                                  cwd='comparative_modelling')

    def test_integrative_modeling_score(self):
        """Test the integrative modeling scoring"""
        # Make sure the script runs without errors
        p = subprocess.check_call(['./run_modeling.py', 'test'],
                                  cwd='integrative_modeling')

    def test_integrative_modeling(self):
        """Test the entire integrative modeling run"""
        import modeller
        # Compile the clustering program
        subprocess.check_call(['gfortran', 'cluster.f', 'u3best.f',
                               '-o', 'cluster.x'],
                              cwd='integrative_modeling/bin')

        # Run sampling
        subprocess.check_call(['./run_modeling.py'],
                              cwd='integrative_modeling')

        # Analysis
        subprocess.check_call(['bin/get_frames.sh'],
                              cwd='integrative_modeling')

        # Make sure that the top three clusters are close to "known good"
        clusters = ['integrative_modeling/clustering/clus.%d.pdb' \
                    % x for x in (1,2,3)]
        exp_clusters = ['model_refinement/cluster%d/model.pdb' \
                        % x for x in (1,2,3)]

        env = modeller.environ()
        n_cluster = 0
        for cluster, exp_cluster in zip(clusters, exp_clusters):
            mc = modeller.model(env, file=cluster)
            s = modeller.selection(mc)
            a = modeller.alignment(env)
            me = modeller.model(env, file=exp_cluster)
            a.append_model(mc, align_codes='clus')
            a.append_model(me, align_codes='exp_clus')
            # We only care about the global (non-cutoff) RMSD, so use a large
            # cutoff so that refine_local doesn't increase the number of
            # equivalent positions at the expense of worsening the RMSD
            r = s.superpose(me, a, rms_cutoff=999.)
            self.assert_(r.rms < 15.0,
                         "RMSD between cluster %d and expected cluster (%.2f) "
                         "is greater than cutoff (%.2f)" \
                         % (n_cluster, r.rms, 15.0))
            n_cluster += 1

    def test_refinement(self):
        """Test the refinement script"""
        # Make sure the script runs without errors
        p = subprocess.check_call(['./model-single.py', '--run_quick_test'],
                                  cwd='model_refinement/cluster1')

if __name__ == '__main__':
    # Always run from top-level directory
    os.chdir(os.path.join(os.path.dirname(sys.argv[0]), '..'))
    unittest.main()
