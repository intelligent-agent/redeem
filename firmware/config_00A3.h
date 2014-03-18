#ifndef FIRMWARE_CONFIG
#define FIRMWARE_CONFIG



/////// CONFIGURATION FOR REPETIER BOARD REV A3 or A3A. ///////

//* Steppers step and direction pins */
//X
#define STEPPER_X_STEP_BANK     	STEPPER_GPIO_0
#define STEPPER_X_STEP_PIN      	27
#define STEPPER_X_DIR_BANK      	STEPPER_GPIO_1
#define STEPPER_X_DIR_PIN       	29
//#define STEPPER_X_DIRECTION     	1   //Set to 1 so that the motor direction is inversed
	
//Y	
#define STEPPER_Y_STEP_BANK     	STEPPER_GPIO_1
#define STEPPER_Y_STEP_PIN      	12
#define STEPPER_Y_DIR_BANK      	STEPPER_GPIO_0
#define STEPPER_Y_DIR_PIN       	22
//#define STEPPER_Y_DIRECTION     	0   //Set to 1 so that the motor direction is inversed
	
//Z	
#define STEPPER_Z_STEP_BANK     	STEPPER_GPIO_0
#define STEPPER_Z_STEP_PIN      	23
#define STEPPER_Z_DIR_BANK      	STEPPER_GPIO_0
#define STEPPER_Z_DIR_PIN       	26
//#define STEPPER_Z_DIRECTION     	0   //Set to 1 so that the motor direction is inversed
	
//E	
#define STEPPER_E_STEP_BANK     	STEPPER_GPIO_1
#define STEPPER_E_STEP_PIN      	28
#define STEPPER_E_DIR_BANK      	STEPPER_GPIO_1
#define STEPPER_E_DIR_PIN       	15
//#define STEPPER_E_DIRECTION     	1   //Set to 1 so that the motor direction is inversed
	
//H	
#define STEPPER_H_STEP_BANK     	STEPPER_GPIO_1
#define STEPPER_H_STEP_PIN      	13
#define STEPPER_H_DIR_BANK      	STEPPER_GPIO_1
#define STEPPER_H_DIR_PIN       	14
//#define STEPPER_H_DIRECTION     	1   //Set to 1 so that the motor direction is inversed

//* End stops pins
#define STEPPER_X_END_MIN_PIN       14
#define STEPPER_X_END_MIN_BANK      GPIO_0_IN

#define STEPPER_Y_END_MIN_PIN       2
#define STEPPER_Y_END_MIN_BANK      GPIO_2_IN

#define STEPPER_Z_END_MIN_PIN       30
#define STEPPER_Z_END_MIN_BANK      GPIO_0_IN

#define STEPPER_X_END_MAX_PIN       21
#define STEPPER_X_END_MAX_BANK      GPIO_3_IN

#define STEPPER_Y_END_MAX_PIN       31
#define STEPPER_Y_END_MAX_BANK      GPIO_0_IN

#define STEPPER_Z_END_MAX_PIN       4
#define STEPPER_Z_END_MAX_BANK      GPIO_0_IN

//* Please put each dir and step pin in the proper buck if they are for GPIO0 or GPIO1 bank. This is a restriction due to the limited capabilities of the pasm preprocessor.
#define GPIO0_MASK          		((1<<STEPPER_Y_DIR_PIN)|(1<<STEPPER_Z_STEP_PIN)|(1<<STEPPER_Z_DIR_PIN)|(1<<STEPPER_X_STEP_PIN))
#define GPIO1_MASK          		((1<<STEPPER_Y_STEP_PIN)|(1<<STEPPER_H_STEP_PIN)|(1<<STEPPER_H_DIR_PIN)|(1<<STEPPER_E_DIR_PIN)|(1<<STEPPER_E_STEP_PIN)|(1<<STEPPER_X_DIR_PIN))

#ifndef INVERSION_MASK
#define INVERSION_MASK 0
#endif

#endif //endif FIRMWARE_CONFIG
