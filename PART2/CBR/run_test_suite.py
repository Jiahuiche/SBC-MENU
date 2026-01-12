#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE CBR TEST RUNNER
==============================

Automated test suite executor for the CBR Menu System.
Supports non-interactive and interactive test execution with input mocking.

Features:
- Loads test_cases_extended.json
- Executes full CBR cycle (Retrieve → Adapt → Revise → Retain)
- Mocks user input for interactive tests
- Validates expected behaviors
- Generates detailed test report

Usage:
    python run_test_suite.py                    # Run all tests
    python run_test_suite.py --verbose          # Verbose output
    python run_test_suite.py --test TEST_001    # Run specific test
    python run_test_suite.py --save-cases       # Allow saving cases to base
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import patch

# Add CBR directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CBR_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'CBR')
sys.path.insert(0, CBR_DIR)

# Import CBR modules
from Retrieve import load_case_base, retrieve_cases
from Adapt import adapt_menu, load_all_knowledge_bases
from Revise import revise_menu
from Retain import retain_case, calculate_similarity_to_base, calculate_novelty, calculate_trace_score

# Paths
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')
TEST_CASES_PATH = os.path.join(SCRIPT_DIR, 'test_cases_extended.json')
RESULTS_PATH = os.path.join(CBR_DIR, 'test_results_extended.json')


# ============================================================================
# TEST EXECUTION
# ============================================================================

def execute_test(
    test_case: Dict,
    case_base: List[Dict],
    restricciones_db: Dict,
    contexto_db: Dict,
    ontologia_db: Dict,
    pairing_db: Dict,
    verbose: bool = False,
    save_cases: bool = False
) -> Dict:
    """
    Executes a single test case through the full CBR cycle.
    
    Returns:
        Dict with test results including pass/fail status and details
    """
    test_id = test_case.get('id', 'UNKNOWN')
    description = test_case.get('description', 'No description')
    user_input = test_case.get('input', {})
    expected = test_case.get('expected', {})
    mock_inputs = test_case.get('mock_user_inputs', None)
    
    result = {
        'test_id': test_id,
        'description': description,
        'status': 'PENDING',
        'passed': False,
        'execution_time': 0,
        'phases': {},
        'validations': {},
        'error': None
    }
    
    start_time = time.time()
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🧪 TEST: {test_id}")
        print(f"{'='*70}")
        print(f"📝 {description}")
        print(f"🔹 Input: {json.dumps(user_input, indent=2)}")
    
    try:
        # ====================================================================
        # SPECIAL CASE: Empty case base test
        # ====================================================================
        if test_id == "TEST_025":
            # Simulate empty case base
            retrieved = retrieve_cases(user_input, [])
            result['phases']['retrieve'] = {
                'found_cases': len(retrieved),
                'top_score': 0
            }
            result['validations']['should_find_case'] = (len(retrieved) == 0)
            result['status'] = 'PASS' if len(retrieved) == 0 else 'FAIL'
            result['passed'] = (len(retrieved) == 0)
            result['execution_time'] = time.time() - start_time
            return result
        
        # ====================================================================
        # PHASE 1: RETRIEVE
        # ====================================================================
        if verbose:
            print(f"\n🔍 RETRIEVE PHASE")
        
        retrieved = retrieve_cases(user_input, case_base)
        
        result['phases']['retrieve'] = {
            'found_cases': len(retrieved),
            'top_score': retrieved[0]['score'] if retrieved else 0,
            'top_case_id': retrieved[0]['case'].get('id_caso') if retrieved else None
        }
        
        if verbose:
            print(f"   Found {len(retrieved)} cases")
            if retrieved:
                print(f"   Top case: ID={retrieved[0]['case'].get('id_caso')} Score={retrieved[0]['score']:.2f}")
        
        # Validation: should_find_case
        if 'should_find_case' in expected:
            result['validations']['should_find_case'] = (len(retrieved) > 0) == expected['should_find_case']
        
        # Validation: min_score
        if 'min_score' in expected and retrieved:
            result['validations']['min_score'] = retrieved[0]['score'] >= expected['min_score']
        
        if not retrieved:
            result['status'] = 'PASS' if not expected.get('should_find_case', True) else 'FAIL'
            result['passed'] = result['status'] == 'PASS'
            result['error'] = "No cases retrieved"
            result['execution_time'] = time.time() - start_time
            return result
        
        best_case = retrieved[0]['case']
        best_compliance = retrieved[0].get('compliance', {})
        
        # ====================================================================
        # PHASE 2: ADAPT
        # ====================================================================
        if verbose:
            print(f"\n🔧 ADAPT PHASE")
        
        # Check if adaptation is needed
        needs_adaptation = not best_compliance.get('meets_all_restrictions', False)
        
        if needs_adaptation:
            adapted_menu, adaptation_steps = adapt_menu(
                best_case['solucion'],
                user_input.get('restrictions', []),
                user_input.get('cuisine', ''),
                restricciones_db,
                contexto_db,
                ontologia_db,
                pairing_db
            )
        else:
            adapted_menu = best_case['solucion']
            adaptation_steps = []
        
        result['phases']['adapt'] = {
            'needed_adaptation': needs_adaptation,
            'steps_count': len(adaptation_steps),
            'substitutions': len([s for s in adaptation_steps if s.get('operation') == 'substituted']),
            'removals': len([s for s in adaptation_steps if s.get('operation') == 'removed']),
            'additions': len([s for s in adaptation_steps if s.get('operation') == 'added'])
        }
        
        if verbose:
            print(f"   Adaptation needed: {needs_adaptation}")
            print(f"   Adaptation steps: {len(adaptation_steps)}")
        
        # Validation: expect_adaptation
        if 'expect_adaptation' in expected:
            result['validations']['expect_adaptation'] = needs_adaptation == expected['expect_adaptation']
        
        # ====================================================================
        # PHASE 3: REVISE
        # ====================================================================
        if verbose:
            print(f"\n✅ REVISE PHASE")
        
        # Check if interactive mode is needed
        is_interactive = (mock_inputs is not None)
        
        if is_interactive:
            # Mock user input
            if verbose:
                print(f"   Interactive mode: Mocking {len(mock_inputs)} inputs")
            
            with patch('builtins.input', side_effect=mock_inputs):
                revision_results = revise_menu(
                    adapted_menu,
                    user_input.get('restrictions', []),
                    user_input.get('cuisine', ''),
                    adaptation_steps,
                    interactive=True
                )
        else:
            # Non-interactive validation
            revision_results = revise_menu(
                adapted_menu,
                user_input.get('restrictions', []),
                user_input.get('cuisine', ''),
                adaptation_steps,
                interactive=False
            )
        
        result['phases']['revise'] = {
            'is_valid': revision_results['is_valid'],
            'violations_count': len(revision_results.get('violations', [])),
            'performance': revision_results.get('performance', 0),
            'rating': revision_results.get('rating'),
            'needs_revision': revision_results.get('needs_revision', False)
        }
        
        if verbose:
            print(f"   Valid: {revision_results['is_valid']}")
            print(f"   Violations: {len(revision_results.get('violations', []))}")
            print(f"   Needs revision: {revision_results.get('needs_revision', False)}")
        
        # Validation: expect_is_valid
        if 'expect_is_valid' in expected:
            result['validations']['expect_is_valid'] = revision_results['is_valid'] == expected['expect_is_valid']
        
        # Validation: expect_needs_revision
        if 'expect_needs_revision' in expected:
            result['validations']['expect_needs_revision'] = revision_results.get('needs_revision', False) == expected['expect_needs_revision']
        
        # ====================================================================
        # PHASE 4: RETAIN
        # ====================================================================
        if verbose:
            print(f"\n💾 RETAIN PHASE")
        
        # Calculate usefulness components
        similarity = calculate_similarity_to_base(
            {
                'problema': user_input,
                'solucion': adapted_menu
            },
            case_base
        )
        
        novelty = calculate_novelty(
            {
                'problema': user_input,
                'solucion': adapted_menu
            },
            case_base
        )
        
        trace = calculate_trace_score(adaptation_steps)
        performance = revision_results.get('performance', 0)
        
        # Calculate usefulness
        usefulness = (
            0.4 * performance +
            0.15 * (1 - similarity) +
            0.25 * novelty +
            0.2 * trace
        )
        
        should_retain = (usefulness >= 0.5) and revision_results['is_valid']
        
        result['phases']['retain'] = {
            'usefulness': usefulness,
            'similarity': similarity,
            'novelty': novelty,
            'trace': trace,
            'performance': performance,
            'should_retain': should_retain
        }
        
        if verbose:
            print(f"   Usefulness: {usefulness:.3f}")
            print(f"   Should retain: {should_retain}")
        
        # Validation: expect_should_retain
        if 'expect_should_retain' in expected:
            result['validations']['expect_should_retain'] = should_retain == expected['expect_should_retain']
        
        # Actually save if enabled and should retain
        if save_cases and should_retain:
            # Note: In production, this would save to the case base
            if verbose:
                print(f"   ⚠️  Case would be saved (save_cases=True)")
        
        # ====================================================================
        # FINAL VALIDATION
        # ====================================================================
        all_validations_pass = all(result['validations'].values())
        result['status'] = 'PASS' if all_validations_pass else 'FAIL'
        result['passed'] = all_validations_pass
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"Result: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
            if not result['passed']:
                print(f"Failed validations:")
                for key, value in result['validations'].items():
                    if not value:
                        print(f"  - {key}: Expected {expected.get(key)}")
        
    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)
        result['passed'] = False
        if verbose:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    result['execution_time'] = time.time() - start_time
    return result


# ============================================================================
# TEST SUITE EXECUTION
# ============================================================================

def run_test_suite(
    verbose: bool = False,
    save_cases: bool = False,
    specific_test: Optional[str] = None
) -> Dict:
    """
    Runs the complete test suite.
    
    Returns:
        Dict with summary of test results
    """
    print("\n" + "="*70)
    print("🧪 CBR MENU SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"📅 Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load test cases
    print(f"\n⏳ Loading test cases from: {TEST_CASES_PATH}")
    try:
        with open(TEST_CASES_PATH, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        test_cases = test_data.get('test_cases', [])
    except FileNotFoundError:
        print(f"❌ ERROR: Test file not found: {TEST_CASES_PATH}")
        return {'error': 'Test file not found'}
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in test file: {e}")
        return {'error': 'Invalid JSON'}
    
    # Filter for specific test
    if specific_test:
        test_cases = [tc for tc in test_cases if tc.get('id') == specific_test]
        if not test_cases:
            print(f"❌ ERROR: Test {specific_test} not found")
            return {'error': 'Test not found'}
    
    print(f"📋 Tests to execute: {len(test_cases)}")
    
    # Load knowledge bases
    print(f"\n⏳ Loading knowledge bases...")
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    print(f"✅ Knowledge bases loaded")
    
    # Load case base
    print(f"\n⏳ Loading case base from: {CASE_BASE_PATH}")
    case_base = load_case_base(CASE_BASE_PATH)
    if not case_base:
        print(f"❌ ERROR: Could not load case base")
        return {'error': 'Case base load failed'}
    print(f"✅ Case base loaded: {len(case_base)} cases")
    
    # Execute tests
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(test_cases),
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'total_time': 0,
        'test_results': []
    }
    
    print(f"\n{'='*70}")
    print("EXECUTING TESTS")
    print("="*70)
    
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case.get('id', f'TEST_{i}')
        
        if not verbose:
            print(f"\n[{i}/{len(test_cases)}] {test_id}...", end=' ')
        
        test_result = execute_test(
            test_case,
            case_base,
            restricciones_db,
            contexto_db,
            ontologia_db,
            pairing_db,
            verbose=verbose,
            save_cases=save_cases
        )
        
        results['test_results'].append(test_result)
        results['total_time'] += test_result['execution_time']
        
        if test_result['status'] == 'PASS':
            results['passed'] += 1
            if not verbose:
                print("✅ PASS")
        elif test_result['status'] == 'FAIL':
            results['failed'] += 1
            if not verbose:
                print("❌ FAIL")
        else:
            results['errors'] += 1
            if not verbose:
                print("⚠️  ERROR")
    
    # Print summary
    print_summary(results, verbose)
    
    # Save results
    save_results(results)
    
    return results


# ============================================================================
# REPORTING
# ============================================================================

def print_summary(results: Dict, verbose: bool = False):
    """Prints test execution summary."""
    print("\n" + "="*70)
    print("📊 TEST EXECUTION SUMMARY")
    print("="*70)
    
    total = results['total_tests']
    passed = results['passed']
    failed = results['failed']
    errors = results['errors']
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Passed:  {passed}/{total} ({pass_rate:.1f}%)")
    print(f"❌ Failed:  {failed}/{total}")
    print(f"⚠️  Errors:  {errors}/{total}")
    print(f"⏱️  Total Time: {results['total_time']:.2f}s")
    
    # Failed tests details
    if failed > 0 or errors > 0:
        print(f"\n{'='*70}")
        print("FAILED/ERROR TESTS DETAILS")
        print("="*70)
        
        for test_result in results['test_results']:
            if test_result['status'] != 'PASS':
                print(f"\n❌ {test_result['test_id']}: {test_result['status']}")
                print(f"   {test_result['description']}")
                
                if test_result.get('error'):
                    print(f"   Error: {test_result['error']}")
                
                # Show failed validations
                for key, passed in test_result.get('validations', {}).items():
                    if not passed:
                        print(f"   ❌ Validation failed: {key}")
    
    # Phase statistics
    if verbose:
        print(f"\n{'='*70}")
        print("PHASE STATISTICS")
        print("="*70)
        
        retrieve_stats = {'found': 0, 'not_found': 0}
        adapt_stats = {'adapted': 0, 'no_adaptation': 0}
        revise_stats = {'valid': 0, 'invalid': 0}
        retain_stats = {'retained': 0, 'not_retained': 0}
        
        for test_result in results['test_results']:
            phases = test_result.get('phases', {})
            
            if 'retrieve' in phases:
                if phases['retrieve']['found_cases'] > 0:
                    retrieve_stats['found'] += 1
                else:
                    retrieve_stats['not_found'] += 1
            
            if 'adapt' in phases:
                if phases['adapt']['needed_adaptation']:
                    adapt_stats['adapted'] += 1
                else:
                    adapt_stats['no_adaptation'] += 1
            
            if 'revise' in phases:
                if phases['revise']['is_valid']:
                    revise_stats['valid'] += 1
                else:
                    revise_stats['invalid'] += 1
            
            if 'retain' in phases:
                if phases['retain']['should_retain']:
                    retain_stats['retained'] += 1
                else:
                    retain_stats['not_retained'] += 1
        
        print(f"\nRetrieve: {retrieve_stats['found']} found, {retrieve_stats['not_found']} not found")
        print(f"Adapt: {adapt_stats['adapted']} adapted, {adapt_stats['no_adaptation']} no adaptation")
        print(f"Revise: {revise_stats['valid']} valid, {revise_stats['invalid']} invalid")
        print(f"Retain: {retain_stats['retained']} retained, {retain_stats['not_retained']} not retained")
    
    print("\n" + "="*70)


def save_results(results: Dict):
    """Saves test results to JSON file."""
    try:
        with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {RESULTS_PATH}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run CBR Menu System Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output with detailed test execution')
    parser.add_argument('--save-cases', '-s', action='store_true',
                        help='Allow saving cases to case base (USE WITH CAUTION)')
    parser.add_argument('--test', '-t', type=str,
                        help='Run specific test by ID (e.g., TEST_001)')
    
    args = parser.parse_args()
    
    results = run_test_suite(
        verbose=args.verbose,
        save_cases=args.save_cases,
        specific_test=args.test
    )
    
    # Exit code based on results
    if results.get('error'):
        sys.exit(2)
    elif results.get('failed', 0) > 0 or results.get('errors', 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
