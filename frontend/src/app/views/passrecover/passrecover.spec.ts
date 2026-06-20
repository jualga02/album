import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Passrecover } from './passrecover';

describe('Passrecover', () => {
  let component: Passrecover;
  let fixture: ComponentFixture<Passrecover>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Passrecover],
    }).compileComponents();

    fixture = TestBed.createComponent(Passrecover);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
