"""Compare alpha silhouettes in an explicitly shared image frame, not quality."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def metrics(reference, candidate):
    if reference.shape != candidate.shape or reference.ndim != 2:
        raise ValueError('Masks must share a two-dimensional frame')
    reference, candidate = reference.astype(bool), candidate.astype(bool)
    if not reference.any() or not candidate.any():
        raise ValueError('Empty silhouettes are not comparable')
    return {'iou': float(np.count_nonzero(reference & candidate) /
                         np.count_nonzero(reference | candidate)),
            'missing_pixels': int(np.count_nonzero(reference & ~candidate)),
            'extra_pixels': int(np.count_nonzero(candidate & ~reference)),
            'quality_accepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--scale', type=float, required=True)
    parser.add_argument('--offset', type=float, nargs=2, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if not np.isfinite([args.scale, *args.offset]).all() or args.scale <= 0:
        parser.error('Transform must be finite with positive scale')
    def alpha(path):
        with Image.open(path) as source:
            if 'A' not in source.getbands():
                raise ValueError('Explicit alpha channel required')
            return source.getchannel('A')
    candidate = alpha(args.candidate)
    reference = alpha(args.reference).transform(candidate.size, Image.Transform.AFFINE,
        (1/args.scale, 0, -args.offset[0]/args.scale,
         0, 1/args.scale, -args.offset[1]/args.scale), resample=Image.Resampling.NEAREST)
    result = metrics(np.asarray(reference)>128, np.asarray(candidate)>128)
    result.update(reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                  candidate_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
                  scale=args.scale, offset=args.offset,
                  scope='Same-view alpha silhouette only; no depth or component validation')
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
