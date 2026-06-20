import { TestBed } from '@angular/core/testing';

import { Albumcalls } from './albumcalls';

describe('Albumcalls', () => {
  let service: Albumcalls;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Albumcalls);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
