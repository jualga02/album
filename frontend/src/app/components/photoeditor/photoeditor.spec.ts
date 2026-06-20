import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Photoeditor } from './photoeditor';

describe('Photoeditor', () => {
  let component: Photoeditor;
  let fixture: ComponentFixture<Photoeditor>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Photoeditor],
    }).compileComponents();

    fixture = TestBed.createComponent(Photoeditor);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
